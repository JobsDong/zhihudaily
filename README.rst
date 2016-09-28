======================
知乎日报网页版
======================

zhihudaily 是基于tornado技术的知乎日报的网页版。部署在sae上。

Demo地址: http://zhihurewen.sinaapp.com


SAE环境搭建
========================

1. 申请sae账户，并且创建python应用

2. 修改配置文件config.py::

    # 配置数据存储引擎（基于kvdb, mysql）
    # 如果是基于mysql，需开通数据库服务、并使用daily.sql初始化表结构
    # 如果是基于kvdb,需开通kvdb服务
    from base.daily_store import DailyStorer

    # sae kvdb数据库存储
    DailyStorer.configure("base.kvdb_store.KvdbStorer")

    # sae mysql数据库存储
    # import sae.const
    # DailyStorer.configure("base.db_store.DatabaseStorer",
    #                        host=sae.const.MYSQL_HOST,
    #                        port=int(sae.const.MYSQL_PORT),
    #                        user=sae.const.MYSQL_USER,
    #                        passwd=sae.const.MYSQL_PASS,
    #                        db=sae.const.MYSQL_DB)


    # operation操作
    # cron操作(采集、建索引)的用户名密码
    username = "admin"
    password = "admin"

    # 图片存储
    # 需要开通scs服务，手动创建bucket
    image_accesskey = ""
    image_secretkey = ""
    image_bucket = "dailyimage"

    # 配置搜索引擎（基于kvdb, whoosh）
    # 需要开通kvdb服务，sae普通用户级别限制太多，数据量多了，会出现被禁止(Demo中使用)
    from search.fts_search import FTSSearcher
    FTSSearcher.configure("search.kvdb_search.KvdbFTSSearcher",
                      name="zhihudaily")

    # 基于Ali open search
    # 需要开通阿里云opensearch服务，并配置app、表结构
    # FTSSearcher.configure("search.ali_search.AliFTSSearcher",
    #                       uri="http://opensearch-cn-hangzhou.aliyuncs.com",
    #                       app="zhihudaily", access_key="fake_key",
    #                       access_secret="fake_secret")


3. 修改sae的配置文件config.yaml::

	# APP NAME
	name: zhihurewen
	# 定时采集
	url: /operation/fetch
	# 定时建立索引
	url: /operation/index

4. 上传代码