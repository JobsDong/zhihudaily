CREATE TABLE IF NOT EXISTS 'news' (
  'id' INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
  'news_id' varchar(50) NOT NULL UNIQUE,
  'title' varchar(200) NOT NULL,
  'share_url' varchar(100) NOT NULL,
  'date' varchar(50) NOT NULL,
  'body' longtext NOT NULL,
  'image' varchar(100) NOT NULL,
  'image_source' varchar(100) NOT NULL,
  'image_public_url' varchar(100) NOT NULL
) DEFAULT CHARSET=utf8;

CREATE INDEX date_index USING BTREE ON 'news'('date');

CREATE INDEX news_id_index USING BTREE ON 'news'('news_id');