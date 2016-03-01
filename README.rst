======================
知乎日报网页版
======================

zhihudaily 是基于tornado技术的知乎日报的网页版。部署在sae上。

Demo地址: http://zhihurewen.sinaapp.com


SAE环境搭建
========================

1. 申请sae账户，并且创建python应用

2. 启动MySQL, Memcache服务, KVDB服务，并创建数据库和表结构

3. 修改配置文件config.py::

    # 用户名/密码
    username = "admin"
    password = "admin"

    # 图片存储的bucket name
    IMAGE_BUCKET = "dailyimage"

    # 配置搜索引擎（基于kvdb, whoosh）由于sae的kvdb有分钟配额限制，数据量稍大就会被禁止
    from search.fts_search import FTSSearcher
    FTSSearcher.configure("search.kvdb_search.KvdbFTSSearcher",
                      name="zhihudaily")

    # 基于Ali open search,
    # FTSSearcher.configure("search.ali_search.AliFTSSearcher",
    #                       uri="http://opensearch-cn-hangzhou.aliyuncs.com",
    #                       app="zhihudaily", access_key="fake_key",
    #                       access_secret="fake_secret")


4. 启动Storage服务，并创建1个Bucket(IMAGE_BUCKET)

5. 修改sae的配置文件config.yaml::

	# APP NAME
	name: zhihurewen
	# 定时采集 url后面的密码
	url: /operation/fetch
	# 定时建立索引
	url: /operation/index

7. 上传代码