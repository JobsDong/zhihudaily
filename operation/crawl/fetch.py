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
from base.daily_store import DailyStorer, News
from search.fts_search import FTSSearcher
from utils.extract_util import extract_text

from sae.storage import Connection


def not_exists_news_ids(date_str, latest_news_ids):
    """找出所有不存在的news_ids

    Args:
      date_str: 日期 %Y%m%d
      latest_news_ids: 最新的news_ids

    Returns:
      list: not_exists_news_ids
    """
    daily_storer = DailyStorer()
    not_exists_news_ids = []
    try:
        exists_news_ids = [str(news.news_id) for news
                           in daily_storer.filter_news_list(date_str)]
        for news_id in latest_news_ids:
            if str(news_id) not in exists_news_ids:
                not_exists_news_ids.append(news_id)
    finally:
        daily_storer.close()
    return not_exists_news_ids


def fetch_news_list(news_ids):
    """获取所有的news，image信息

    Args:
      news_ids: 需要采集的newsid

    Returns:
      wait_for_store_news_list: 需要保存的news列表

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
    fts_indexer = FTSSearcher()
    try:
        news_docs = []
        for news in news_list:
            body_text = extract_text(news.get('body', ''))
            news_docs.append(dict(news_id=news['news_id'], title=news['title'],
                                  content=body_text))
        fts_indexer.add_many_docs(news_docs)
    finally:
        fts_indexer.close()


def get_news_list(date_str):
    daily_storer = DailyStorer()
    news_list = []
    try:
        wait_for_indexed_news_list = daily_storer.filter_news_list(date_str)
        for news in wait_for_indexed_news_list:
            news_list.append(dict(news_id=news.news_id, title=news.title,
                                  body=news.body))
        return news_list
    finally:
        daily_storer.close()


def store_news_list(news_list):
    """将news_list保存到数据库中
    """
    daily_storer = DailyStorer()
    try:
        for news_json in news_list:
            daily_storer.add_news(News(
                news_json['news']['id'],
                news_json['news']['share_url'],
                news_json['news']['title'],
                news_json['date_str'],
                news_json['news']['body'],
                news_json['news']['image'],
                news_json['news'].get('image_source', ''),
                news_json['public_image_url'],

            ))
    finally:
        daily_storer.close()


def fetch_image(news_url, image_url):
    """获取图片内容
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
    """
    news_ids = []

    stories = latest_news['stories']
    for story in stories:
        news_ids.append(story['id'])

    return news_ids


def extract_date_str(latest_news):
    """提取出最新的日期
    """
    return latest_news['date']
