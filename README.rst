======================
知乎日报网页版
======================

zhihudaily 是基于tornado技术的知乎日报的网页版。部署在sae上。

Demo地址: http://zhihurewen.sinaapp.com


本地测试环境搭建以及运行
========================================

1. 安装依赖
	pip install -r requirements.txt

2. 创建表结构::

	CREATE TABLE IF NOT EXISTS `news` (
    `id` INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `news_id` varchar(50) NOT NULL UNIQUE,
    `title` varchar(200) NOT NULL,
    `share_url` varchar(100) NOT NULL,
    `date` varchar(50) NOT NULL,
    `body` longtext NOT NULL,
    `image` varchar(100) NOT NULL,
    `image_source` varchar(100) NOT NULL,
    `image_public_url` varchar(100) NOT NULL
    ) DEFAULT CHARSET=utf8;

	CREATE INDEX date_index USING BTREE ON `news`(`date`);

	CREATE INDEX news_id_index USING BTREE ON `news`(`news_id`);

3. 修改配置文件config.py::

	# 密码(311521)的md5
    secret = "76a4cebbe7af10ffd169cd9494adcf2f"
	# 修改debug模式中的数据库配置
    DB_HOST = "127.0.0.1"
	DB_NAME = "daily"
	DB_USER = "root"
	DB_PASS = "root"
	DB_PORT = 3306
	MEMCACHE_HOST = "127.0.0.1"


4. 运行::

	python index.wsgi --port=8080


SAE环境搭建
========================

1. 申请sae账户，并且创建python应用

2. 启动MySQL, Memcache服务，并创建数据库和表结构

3. 修改配置文件config.py::

	# 密码(311521)的md5
	secret = "76a4cebbe7af10ffd169cd9494adcf2f"

	# 索引目录名
	index_dir = 'dailyindex'

	# 图片存储的bucket name
	IMAGE_BUCKET = "dailyimage"

	# 索引保存的bucket name
	FS_BUCKET = "dailyfiles"

4. 启动Storage服务，并创建2个Bucket(IMAGE_BUCKET, FS_BUCKET)

5. 修改sae的配置文件config.yaml::

	# APP NAME
	name: zhihurewen
	# 定时采集 url后面的密码
	url: /operation/fetch?secret=311521
	# 定时建立索引
	url: /operation/index?secret=311521

7. 上传代码


注意
==============

1. 本地测试环境中，数据不会自动采集，可以手动启动采集当天的数据
	"http://localhost:{port}/operation/fetch?secret={secret}

2. 本地测试环境，采集某一天的数据
	"http://localhost:{port}/operation/fetch?date=20140808&secret={secret}

3. 本地测试环境，数据不会自动建立索引，可以手动启动建立索引
	"http://localhost:{port}/operation/index?secret={secret}

4. 本地测试环境，对某一天建立索引
	"http://localhost:{port}/opertion/index?date=20140808&secret={secret}

5. sae中有定时任务Cron。每隔1小时，会采集最新数据并更新，可在config.yaml的cron修改