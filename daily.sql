CREATE TABLE IF NOT EXISTS 'newses' (
  'id' INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
  'news_id' varchar(50) NOT NULL UNIQUE,
  'title' varchar(256) NOT NULL,
  'share_url' varchar(128) NOT NULL,
  'date' varchar(64) NOT NULL,
  'body' longtext NOT NULL,
  'image' varchar(128) NOT NULL,
  'image_source' varchar(128) NOT NULL,
  'image_public_url' varchar(128) NOT NULL
) DEFAULT CHARSET=utf8;

CREATE INDEX date_newses_index USING BTREE ON 'newses'('date');

CREATE INDEX news_id_newses_index USING BTREE ON 'newses'('news_id');