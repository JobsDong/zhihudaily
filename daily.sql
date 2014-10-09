PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE news (
'id' varchar(50) NOT NULL,
'title' varchar(50) NOT NULL,
'share_url' varchar(50) NOT NULL,
'date' varchar(50) NOT NULL,
'body' text NOT NULL,
'image' varchar(100) NOT NULL,
'image_source' varchar(50) NOT NULL,
PRIMARY KEY ('id'));
COMMIT;
