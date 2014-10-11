CREATE TABLE IF NOT EXISTS `news` (
`id` varchar(50) NOT NULL,
`title` varchar(100) NOT NULL,
`share_url` varchar(100) NOT NULL,
`date` varchar(50) NOT NULL,
`body` text NOT NULL,
`image` varchar(100) NOT NULL,
`image_source` varchar(100) NOT NULL,
`image_public_url` varchar(100) NOT NULL,
`insert_time` timestamp NOT NULL,
PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;