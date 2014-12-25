#!/usr/bin/python
# -*- coding=utf-8 -*-

"""运维操作
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import traceback
import logging
import urlparse
import hashlib
import httplib

from config import debug, IMAGE_BUCKET
import daily
import database
from search import fts
import util

if debug:
    from util import Connection
else:
    from sae.storage import Connection


class OperationException(Exception):

    def __init__(self, msg):
        super(OperationException, self).__init__(msg)


class operation_route(object):
    """operation的包装起
    """

    _operation_methods = {}

    def __init__(self, uri):
        self._uri = uri

    def __call__(self, route_method):
        self._operation_methods[self._uri] = route_method

    @classmethod
    def get_operation_routes(cls):
        return cls._operation_methods


@operation_route(r"/operation/fetch_before")
def fetch_before(params):
    """下载某天的新闻，并保存

    :param params:
    :return:
    """
    if 'date' not in params:
        raise OperationException("lack of param date")

    date_str = params['date'][0]
    zh = daily.ZhiHu()

    # 获取最新的news_id列表
    latest_news = zh.get_before_news(date_str)
    news_ids = _extract_news_ids(latest_news)
    date_str = _extract_date_str(latest_news)

    # 找出数据库中没有的news_id列表
    not_exists_news_ids = _not_exists_news_ids(date_str, news_ids)

    # 获取news和下载图片
    not_exists_news_ids.reverse()
    wait_for_store_news_list = _get_news_list(not_exists_news_ids)

    # 保存图片
    wait_for_store_news_list = _store_images(wait_for_store_news_list, date_str)

    # 保存news到数据库中
    _store_news_list(wait_for_store_news_list)

    # 创建索引
    _index_news_list([wait_for_store_news['news'] for wait_for_store_news
                      in wait_for_store_news_list])


@operation_route(r"/operation/fetch_latest")
def fetch_latest(params):
    """下载最新的新闻（包括图片），并保存

    :return:
    """
    zh = daily.ZhiHu()

    # 获取最新的news_id列表
    latest_news = zh.get_latest_news()
    latest_news_ids = _extract_news_ids(latest_news)
    date_str = _extract_date_str(latest_news)

    # 找出数据库中没有的news_id列表
    not_exists_news_ids = _not_exists_news_ids(date_str, latest_news_ids)

    # 获取news和下载图片
    not_exists_news_ids.reverse()
    wait_for_store_news_list = _get_news_list(not_exists_news_ids)

    # 保存图片
    wait_for_store_news_list = _store_images(wait_for_store_news_list, date_str)

    # 保存news到数据库中
    _store_news_list(wait_for_store_news_list)

    # 创建索引
    _index_news_list([wait_for_store_news['news'] for wait_for_store_news
                      in wait_for_store_news_list])


def _not_exists_news_ids(date_str, latest_news_ids):
    """找出所有不存在的news_ids

    :param date_str:
    :param latest_news_ids:
    :return:
    """
    dao = database.Dao()
    not_exists_news_ids = []
    try:
        exists_news_ids = [str(news[1]) for news
                           in dao.select_news_list(date_str)]
        for news_id in latest_news_ids:
            if news_id not in exists_news_ids:
                not_exists_news_ids.append(news_id)
    finally:
        dao.close()
    return not_exists_news_ids


def _get_news_list(news_ids):
    """获取所有的news，image信息

    :param news_ids:
    :return:
    """
    zh = daily.ZhiHu()

    wait_for_store_news_list = []
    for news_id in news_ids:
        try:
            news = zh.get_news(news_id)
            # 下载图片
            image_url = news['image'] if 'image' in news else news['theme_image']
            image_type, image_data = _fetch_image(news['share_url'], image_url)

            wait_for_store_news_list.append(dict(news=news,
                                                 image_type=image_type,
                                                 image_data=image_data,
                                                 image_url=image_url))
        except Exception as e:
            stack = traceback.format_exc()
            logging.error("fetch latest error %s\n%s" % (e, stack))

    return wait_for_store_news_list


def _index_news_list(news_list):
    for news in news_list:
        body_text = util.extract_text(news.get('body', ''))
        fts.add_doc(str(news['id']), news['title'], body_text)


def _store_news_list(news_list):
    """将news_list保存到数据库中

    :param news_list:
    :return:
    """
    dao = database.Dao()
    try:
        for news in news_list:
            dao.insert(news['public_image_url'],
                       news['date_str'],
                       news['news'])
    finally:
        dao.close()


def _fetch_image(news_url, image_url):
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


def _store_images(news_list, date_str):
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
        con.put_object(IMAGE_BUCKET, object_name, image_data, image_type)
        public_image_url = con.generate_url(IMAGE_BUCKET, object_name)

        a_news_copy['public_image_url'] = public_image_url
        a_news_copy['date_str'] = date_str
        news_list_copy.append(a_news_copy)

    return news_list_copy


def _extract_news_ids(latest_news):
    """提取出最新的news_ids

    :param latest_news:
    :return:
    """
    news_ids = []

    stories = latest_news['stories']
    for story in stories:
        news_ids.append(story['id'])

    return news_ids


def _extract_date_str(latest_news):
    """提取出最新的日期

    :param latest_news:
    :return:
    """
    return latest_news['date']


if __name__ == "__main__":
    fetch_latest(None)
