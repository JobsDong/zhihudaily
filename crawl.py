#!/usr/bin/python
# -*- coding=utf-8 -*-

"""数据采集
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from config import debug, BUCKET

import urlparse

import hashlib
import httplib
import daily
import model

if debug:
	pass
else:
	from sae.storage import Connection


def fetch_before(date_str):
	"""下载某天的新闻，并保存

	:param date_str:
	:return:
	"""
	zh = daily.ZhiHu()
	dao = model.Dao()
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
				image_type, image_data = _fetch_image(news['share_url'], news['image'])
				# 存储图片
				public_image_url = _store_image(news['image'], image_type, image_data)
				dao.insert(public_image_url, date_str, news)
			except Exception as e:
				print e
	finally:
		dao.close()


def fetch_latest():
	"""下载最新的新闻（包括图片），并保存

	:return:
	"""
	zh = daily.ZhiHu()
	dao = model.Dao()

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
				image_type, image_data = _fetch_image(news['share_url'], news['image'])
				# 存储图片
				public_image_url = _store_image(news['image'], image_type, image_data)
				dao.insert(public_image_url, date_str, news)
			except Exception as e:
				print e

	finally:
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
		print story['id'], story['title']
		news_ids.append(story['id'])

	return news_ids


def _extract_date_str(latest_news):
	"""提取出最新的日期

	:param latest_news:
	:return:
	"""
	return latest_news['date']


if __name__ == "__main__":
	fetch_latest()