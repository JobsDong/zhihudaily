======================
知乎日报网页版
======================

zhihudaily 是基于tornado技术的知乎日报的网页版。部署在sae上。

Demo地址: http://zhihurewen.sinaapp.com


SAE环境搭建
========================

1. 申请sae账户，并且创建python应用

2. 启动MySQL, Memcache服务，并创建数据库和表结构

3. 修改配置文件config.py::

	# 用户名/密码
	username = "admin"
	password = "admin"

	# 图片存储的bucket name
	IMAGE_BUCKET = "dailyimage"

	# ali open search host, app , access_key, access_secret
	ALI_SEARCH_HOST = "http://opensearch-cn-hangzhou.aliyuncs.com"
	ALI_SEARCH_APP = "zhihudaily"
	ACCESS_KEY = "fake_key"
	ACCESS_SECRET = "fake_secret"

4. 启动Storage服务，并创建1个Bucket(IMAGE_BUCKET)

5. 修改sae的配置文件config.yaml::

	# APP NAME
	name: zhihurewen
	# 定时采集 url后面的密码
	url: /operation/fetch
	# 定时建立索引
	url: /operation/index

7. 上传代码