#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import httplib
import urlparse
import traceback
import logging
import hashlib
import config
import zhihu
from daily.dao import DailyDao
from search.ali_search import AliFTSIndexer
from utils.extract_util import extract_text

from sae.storage import Connection


def not_exists_news_ids(date_str, latest_news_ids):
    """找出所有不存在的news_ids

    :param date_str:
    :param latest_news_ids:
    :return:
    """
    dao = DailyDao(config.DB_HOST, config.DB_PORT, config.DB_USER,
                   config.DB_PASS, config.DB_NAME)
    not_exists_news_ids = []
    try:
        exists_news_ids = [str(news[1]) for news
                           in dao.get_news_list(date_str)]
        for news_id in latest_news_ids:
            if str(news_id) not in exists_news_ids:
                not_exists_news_ids.append(news_id)
    finally:
        dao.close()
    return not_exists_news_ids


def fetch_news_list(news_ids):
    """获取所有的news，image信息

    :param news_ids:
    :return:
    """
    zh = zhihu.ZhiHu()

    wait_for_store_news_list = []
    for news_id in news_ids:
        try:
            news = zh.get_news(news_id)
            # 下载图片
            image_url = news['image'] if 'image' in news else news['theme_image']
            image_type, image_data = fetch_image(news['share_url'], image_url)

            wait_for_store_news_list.append(dict(news=news,
                                                 image_type=image_type,
                                                 image_data=image_data,
                                                 image_url=image_url))
        except Exception as e:
            stack = traceback.format_exc()
            logging.error("fetch latest error %s\n%s" % (e, stack))

    return wait_for_store_news_list


def index_news_list(news_list):
    fts_indexer = AliFTSIndexer(config.ALI_SEARCH_HOST, config.ALI_SEARCH_APP,
                                config.ACCESS_KEY, config.ACCESS_SECRET)
    news_docs = []
    for news in news_list:
        body_text = extract_text(news.get('body', ''))
        news_docs.append(dict(news_id=news['news_id'], title=news['title'],
                              content=body_text))
    fts_indexer.add_many_docs(news_docs)


def get_news_list(date_str):
    dao = DailyDao(config.DB_HOST, config.DB_PORT, config.DB_USER,
                   config.DB_PASS, config.DB_NAME)
    news_list = []
    try:
        wait_for_indexed_news_list = dao.get_news_list(date_str)
        for news in wait_for_indexed_news_list:
            news_list.append(dict(news_id=news[1], title=news[2], body=news[5]))
        return news_list
    finally:
        dao.close()


def store_news_list(news_list):
    """将news_list保存到数据库中

    :param news_list:
    :return:
    """
    dao = DailyDao(config.DB_HOST, config.DB_PORT, config.DB_USER,
                   config.DB_PASS, config.DB_NAME)
    try:
        for news in news_list:
            dao.insert(news['public_image_url'],
                       news['date_str'],
                       news['news'])
    finally:
        dao.close()


def fetch_image(news_url, image_url):
    """获取图片内容

    :param news_url:
    :param image_url:
    :return:
    """
    _, host_port, path, _, _ = urlparse.urlsplit(image_url)
    host_port = host_port.split(":")
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 80

    http = httplib.HTTPConnection(host, port, timeout=10)
    http.request("GET", path, headers={"Referer": news_url})
    response = http.getresponse()
    if response.status / 100 == 2:
        data = response.read()
        return response.getheader("content-type"), data
    else:
        return None, None


def store_images(news_list, date_str):
    """保存images

    :param news_list:
    :param date_str:
    :return:
    """
    con = Connection()
    news_list_copy = []
    for news in news_list:
        a_news_copy = dict(news.items())
        image_type = a_news_copy.pop('image_type')
        image_data = a_news_copy.pop('image_data')
        image_url = a_news_copy.pop('image_url')
        # 保存image
        object_name = hashlib.md5(image_url).hexdigest()
        con.put_object(config.IMAGE_BUCKET, object_name, image_data, image_type)
        public_image_url = con.generate_url(config.IMAGE_BUCKET, object_name)

        a_news_copy['public_image_url'] = public_image_url
        a_news_copy['date_str'] = date_str
        news_list_copy.append(a_news_copy)

    return news_list_copy


def extract_news_ids(latest_news):
    """提取出最新的news_ids

    :param latest_news:
    :return:
    """
    news_ids = []

    stories = latest_news['stories']
    for story in stories:
        news_ids.append(story['id'])

    return news_ids


def extract_date_str(latest_news):
    """提取出最新的日期

    :param latest_news:
    :return:
    """
    return latest_news['date']
