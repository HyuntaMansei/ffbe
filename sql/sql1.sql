show databases;
create DATABASE ffbe;
use ffbe;
show tables;
drop table version_info;
truncate table version_info;
create TABLE version_info
(	
	seq	INT NOT NULL AUTO_INCREMENT,
	version VARCHAR(20),
	psword VARCHAR(20),
	PRIMARY KEY(seq) 
);
desc version_info;
INSERT into version_info (version, psword) values
('0.1', 'leonis');
select * from version_info;
select * from version_info ORDER BY seq desc limit 1;

drop table operation_list;
create table operation_list
(
	seq INT NOT NULL AUTO_INCREMENT,
    operation_description VARCHAR(200),
    function_name VARCHAR(200),
    PRIMARY KEY(seq)
    );
desc operation_list;
TRUNCATE operation_list;
insert into operation_list (operation_description, function_name) values
('퀘스트', 'quest'),
('멀티(호스트)', 'multi'),
('멀티(클라)', 'multi_client_any'),
('멀티(클라-특정)', 'multi_client');
select * from operation_list;

DROP TABLE user_log;
CREATE TABLE user_log(
	seq INT NOT NULL AUTO_INCREMENT,
    user_ip char(200),
    order_date DATETIME,
    order_button char(200),
    PRIMARY KEY(seq)
);

DESC user_log;
TRUNCATE user_log;
INSERT INTO user_log (user_ip, order_date, order_button) values
('1.1.1.1', now(), "me");
SELECT * from vc_for_job_list;
desc vc_for_job_list;

create table test_tb as (select * from vc_for_job_list);

select * from vc_for_job_list;
select * from vc_for_job_for_update_list;
truncate vc_for_job_for_update_list;

select distinct char_element from char_list;
update char_list_for_update
set char_element = 
	CASE char_element
		WHEN '어둠' THEN '암'
        WHEN '흙' THEN '토'
        WHEN '빛' THEN '명'
        WHEN '우뢰' THEN '뇌'
		WHEN '뢰' THEN '뇌'
        WHEN '얼음' THEN '빙'
        WHEN '바람' THEN '풍'
        WHEN '물' THEN '수'
        WHEN '불' THEN '화'
        ELSE char_element
	END;

TRUNCATE TABLE IF EXISTS char_list_for_update;
update char_list_for_update
set char_main_job = 
	case char_main_job
		when 'Monk' then '몽크'
        else char_main_job
	END;

select * from job_list;
select * from char_list_for_update;

select char_trsl_name, char_main_job from char_list_for_update where char_main_job_class is Null;

update char_list_for_update
set char_main_job_class = 
	(select class_name from job_list where job_trsl_name = char_main_job),
	char_main_job_class_alias = 
	(select class_name_alias from job_list where job_trsl_name = char_main_job);
select * from char_list_for_update;

use ffbe;
select * from char_list;
CREATE table char_list_for_update;
(select * from char_list);
select * from char_list_for_update;
truncate char_list_for_update;

INSERT IGNORE INTO job_list (job_trsl_name, class_name, class_name_alias)
SELECT job_trsl_name, class_name, class_name_alias 
FROM job_list_for_update;

create TABLE element_list
(	
	seq	INT NOT NULL AUTO_INCREMENT,
	ele_name VARCHAR(20),
	ele_img_source VARCHAR(200),
	PRIMARY KEY(seq) 
);
select * from element_list;
create table job_list_for_update(
select * from job_list);
select * from job_list_for_update;
UPDATE job_list_for_update as u SET
class_name = (select distinct class_name from job_list as o where o.class_name_alias = u.class_name_alias);
truncate job_list_for_update;

select * from job_list;
select * from char_list;
select * from job_list_for_update; 

truncate job_list;

update char_list as t
join job_list as s
ON t.char_main_job = s.job_trsl_name
SET t.char_main_job_class = s.class_name,
t.char_main_job_class_alias = s.class_name_alias
WHERE t.char_main_job_class IS NULL;

select * from char_list where char_main_job_class is NULL;
select * from job_list;

select * from char_list where char_main_job = '사무라이';

use ffbe;
select * from operation_list;

select * from operation_list;
SELECT * FROM test_tb;
SELECT *, COUNT(*) FROM test_tb GROUP BY seq HAVING COUNT(*) > 1;
SELECT * FROM char_list;version_info
SELECT char_element,  FROM char_list 
truncate char_list;
select * from vc_list;
truncate vc_list;
select * from operation_list;
