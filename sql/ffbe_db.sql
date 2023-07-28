use ffbe;
DROP TABLE IF EXISTS char_list;
TRUNCATE TABLE char_list;
CREATE TABLE char_list(
	seq INT NOT NULL AUTO_INCREMENT,
    char_name char(200),
    char_alias char(200),
    char_formal_name char(200),
    char_img_src char(200),
    char_img LONGBLOB,
    char_eval char(200),
	char_rarity char(200),
	char_property char(200),
	char_property_img_src char(200),
    char_property_img LONGBLOB,
	char_main_job char(200),
    char_main_job_class1 char(200),
    char_main_job_class2 char(200),
	char_sub_job1 char(200),
	char_sub_job2 char(200),
    PRIMARY KEY(seq)
    );
ALTER TABLE char_list
ADD CONSTRAINT char_name_unique UNIQUE (char_name);
SELECT * FROM char_list;
SELECT char_img from char_list where char_name = '세피로스';
SELECT char_img from char_list where seq = 2;
SELECT * FROM char_list WHERE char_name LIKE '%천검기%';
DROP TABLE class_list;
CREATE TABLE class_list(
	seq INT NOT NULL AUTO_INCREMENT,
	class_name char(200) UNIQUE,
    class_alias char(200) UNIQUE,
    PRIMARY KEY(seq)
    );
SELECT * from class_list;
TRUNCATE class_list;

DROP TABLE IF EXISTS job_list;
CREATE TABLE job_list(
	seq INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    job_name CHAR(200) UNIQUE,
    job_formal_name CHAR(200) UNIQUE,
    class_name char(200),
    class_alias char(200)
    -- CONSTRAINT fk_job_class FOREIGN KEY (class_name) REFERENCES class_list (class_name)
    );
SELECT * FROM job_list;
TRUNCATE job_list;

SELECT char_name, char_main_job FROM character_list;
UPDATE character_list 
SET char_main_job_class1 = 'temp', char_main_job_class2 = 'temp2' 
WHERE char_name = '세피로스';

SELECT * from char_list where char_main_job_class1 IS NULL;
SELECT * from char_list where char_main_job_class1 = '검';
update char_list SET char_main_job_class1 = '도검', char_main_job_class2 = '도검' where char_main_job_class1 = '검';
SELECT * from class_list;
select * from job_list;
update job_list set class_name = '도검', class_alias = '도검' where class_name = '검';

select * from char_list where char_main_job like '%견습%';
SELECT * FROM char_list WHERE char_main_job LIKE '%그란셸트%';
SELECT * from job_list;
select char_name, char_main_job, char_main_job_class1 from char_list where char_main_job_class1 LIKE '도검';
SELECT char_name, char_main_job, char_main_job_class1 FROM char_list;

select * from char_list;
select * from char_list where char_main_job_class2 = '검①';
select * from char_list where char_main_job_class2 = '검②';
select * from char_list where char_main_job_class2 = '검②';
update char_list set char_main_job_class2 = '검2' where char_main_job_class1 LIKE '검(전%';

UPDATE char_list
SET char_main_job_class2 = REPLACE(char_main_job_class2, '①', '1');
UPDATE char_list
SET char_main_job_class2 = REPLACE(char_main_job_class2, '②', '2');

SELECT * from class_list;
UPDATE class_list SET class_alias = replace(class_alias, '①', '1');
UPDATE class_list SET class_alias = replace(class_alias, '②', '2');

SELECT * from job_list;
UPDATE job_list SET class_alias = replace(class_alias, '①', '1');
UPDATE job_list SET class_alias = replace(class_alias, '②', '2');

CREATE TABLE vc_class_tb(
	seq INT NOT NULL AUTO_INCREMENT,
    vc_name char(120),
    PRIMARY KEY(seq)
);
desc vc_class_tb;

ALTER TABLE `ffbe`.`vc_class_tb` 
ADD COLUMN `vc_img_src` VARCHAR(200) NULL AFTER `vc_name`;
ADD COLUMN `검1` BOOLEAN NULL AFTER `vc_img_src`;
ADD COLUMN `검2` BOOLEAN NULL AFTER `검1`,
ADD COLUMN `검3` BOOLEAN NULL AFTER `검2`,
ADD COLUMN `지팡이1` BOOLEAN NULL AFTER `검3`,
ADD COLUMN `지팡이2` BOOLEAN NULL AFTER `지팡이1`,
ADD COLUMN `대검` BOOLEAN NULL AFTER `지팡이2`,
ADD COLUMN `창` BOOLEAN NULL AFTER `대검`,
ADD COLUMN `도끼` BOOLEAN NULL AFTER `창`,
ADD COLUMN `활` BOOLEAN NULL AFTER `도끼`,
ADD COLUMN `총` BOOLEAN NULL AFTER `활`,
ADD COLUMN `주먹` BOOLEAN NULL AFTER `총`,
ADD COLUMN `단검` BOOLEAN NULL AFTER `주먹`,
ADD COLUMN `닌자` BOOLEAN NULL AFTER `단검`,
ADD COLUMN `도검` BOOLEAN NULL AFTER `닌자`,
ADD COLUMN `메이스` BOOLEAN NULL AFTER `도검`,
ADD COLUMN `글로브` BOOLEAN NULL AFTER `메이스`,
ADD COLUMN `책` BOOLEAN NULL AFTER `글로브`,
ADD COLUMN `부메랑` BOOLEAN NULL AFTER `책`;

select * from char_list;
select * from job_list;
select * from class_list;
select * from vc_for_job_list;

UPDATE job_list SET class_alias = replace(class_alias, '장갑', '글로브');
UPDATE char_list SET char_main_job_class2 = replace(char_main_job_class2, '장갑', '글로브');

UPDATE job_list SET class_alias = replace(class_alias, "③", "3");
select class_alias from class_list;

select vc_name, vc_img_src, g8_link from vc_for_job_list where `검1`=0 and `검2`=0 and `검3`=1;
select * from vc_for_job_list where 검1=0 and 검2=0 and 검3=1 and 총=1;

CREATE TABLE `vc_for_job_for_update_list` (
  `seq` int(11) NOT NULL AUTO_INCREMENT,
  `vc_jp_name` char(120) DEFAULT NULL,
  `vc_g8_link` char(120) DEFAULT NULL,
  `vc_img_src` varchar(200) DEFAULT NULL,
  `검1` tinyint(1) DEFAULT NULL,
  `검2` tinyint(1) DEFAULT NULL,
  `검3` tinyint(1) DEFAULT NULL,
  `지팡이1` tinyint(1) DEFAULT NULL,
  `지팡이2` tinyint(1) DEFAULT NULL,
  `대검` tinyint(1) DEFAULT NULL,
  `창` tinyint(1) DEFAULT NULL,
  `도끼` tinyint(1) DEFAULT NULL,
  `활` tinyint(1) DEFAULT NULL,
  `총` tinyint(1) DEFAULT NULL,
  `주먹` tinyint(1) DEFAULT NULL,
  `단검` tinyint(1) DEFAULT NULL,
  `닌자` tinyint(1) DEFAULT NULL,
  `도검` tinyint(1) DEFAULT NULL,
  `메이스` tinyint(1) DEFAULT NULL,
  `글로브` tinyint(1) DEFAULT NULL,
  `책` tinyint(1) DEFAULT NULL,
  `부메랑` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

truncate table vc_for_job_list;
select * from vc_for_job_list;
truncate table vc_for_job_for_update_list;
select * from vc_for_job_for_update_list;

select * from class_list;

INSERT INTO `ffbe`.`vc_for_job_list`
(`vc_trsl_name`,`vc_jp_name`,`vc_g8_link`,`vc_img_src`,`검1`,`검2`,`검3`,`지팡이1`,`지팡이2`,`대검`,`창`,`도끼`,`활`,`총`,`주먹`,`단검`,`닌자`,`도검`,`메이스`,`글로브`,`책`,`부메랑`)
select `vc_trsl_name`,`vc_jp_name`,`vc_g8_link`,`vc_img_src`,`검1`,`검2`,`검3`,`지팡이1`,`지팡이2`,`대검`,`창`,`도끼`,`활`,`총`,`주먹`,`단검`,`닌자`,`도검`,`메이스`,`글로브`,`책`,`부메랑` 
from vc_for_job_for_update_list;