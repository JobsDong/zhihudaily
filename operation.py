#!/usr/bin/python
# -*- coding=utf-8 -*-

"""运维操作
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import os
import logging
import urlparse
import hashlib
import httplib

from config import debug, BUCKET
import daily
import database
import search
import util


if debug:
    from config import static_path

    class Connection(object):
        """本地化的Storage服务
        """

        def put_object(self, bucket_name, object_name, image_data, image_type):
            bucket_dir = os.path.join(static_path, bucket_name)
            if not os.path.exists(bucket_dir):
                os.mkdir(bucket_dir)
            with open(os.path.join(bucket_dir, object_name),
                      "wb") as object_file:
                object_file.write(image_data)

        def generate_url(self, bucket_name, object_name):
            return "/static/%s/%s" % (bucket_name, object_name)
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
    dao = database.Dao()
    fts = search.FTS()
    try:
        # 获取最新的news_id列表
        latest_news = zh.get_before_news(date_str)
        news_ids = _extract_news_ids(latest_news)
        date_str = _extract_date_str(latest_news)

        # 找出数据库中没有的news_id列表
        not_exists_news_ids = []
        for news_id in news_ids:
            if not dao.exist(news_id):
                not_exists_news_ids.append(news_id)

        # 获取news, 并保存到数据库
        not_exists_news_ids.reverse()
        for news_id in not_exists_news_ids:
            try:
                news = zh.get_news(news_id)
                # 下载图片
                image_url = news['image'] if 'image' in news else news['theme_image']
                image_type, image_data = _fetch_image(news['share_url'], image_url)
                # 存储图片
                public_image_url = _store_image(news['image'], image_type, image_data)
                dao.insert(public_image_url, date_str, news)
                # 创建索引
                body_text = util.extract_text(news.get('body', ''))
                fts.add_doc(str(news['id']), news['title'], body_text)
            except Exception as e:
                logging.error("fetch before error", e)
    finally:
        dao.close()
        fts.close()


@operation_route(r"/operation/fetch_latest")
def fetch_latest(params):
    """下载最新的新闻（包括图片），并保存

    :return:
    """
    zh = daily.ZhiHu()
    dao = database.Dao()
    fts = search.FTS()

    try:
        # 获取最新的news_id列表
        latest_news = zh.get_latest_news()
        news_ids = _extract_news_ids(latest_news)
        date_str = _extract_date_str(latest_news)

        # 找出数据库中没有的news_id列表
        not_exists_news_ids = []
        for news_id in news_ids:
            if not dao.exist(news_id):
                not_exists_news_ids.append(news_id)

        # 获取news, 并保存到数据库
        not_exists_news_ids.reverse()
        for news_id in not_exists_news_ids:
            try:
                news = zh.get_news(news_id)
                # 下载图片
                image_url = news['image'] if 'image' in news else news['theme_image']
                image_type, image_data = _fetch_image(news['share_url'], image_url)
                # 存储图片
                public_image_url = _store_image(image_url, image_type, image_data)
                dao.insert(public_image_url, date_str, news)
                # 创建索引
                body_text = util.extract_text(news.get('body', ''))
                fts.add_doc(str(news['id']), news['title'], body_text)
            except Exception as e:
                logging.error("fetch latest error", e)
    finally:
        fts.close()
        dao.close()

@operation_route(r"/operation/recreate_index")
def recreate_index(params):
    """重建索引

    :param params:
    :return:
    """
    dao = database.Dao()
    fts = search.FTS()
    try:
        # clearing index
        fts.clear()

        # create
        for news in dao.all_news_list():
            try:
                news_id = news[1]
                news_title = news[2]
                body_text = util.extract_text(news[5])
                fts.add_doc(str(news_id), news_title, body_text)
            except Exception as e:
                logging.error("index error", e)
    finally:
        fts.close()
        dao.close()


def _fetch_image(news_url, image_url):
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


def _store_image(image_url, image_type, image_data):
    """保存图片信息，并返回外链

    :param image_url:
    :param image_type:
    :param image_data:
    :return:
    """
    con = Connection()

    m = hashlib.md5()
    m.update(image_url)
    object_name = m.hexdigest()
    con.put_object(BUCKET, object_name, image_data, image_type)

    return con.generate_url(BUCKET, object_name)


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
