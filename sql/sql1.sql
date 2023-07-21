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
SELECT * from user_log;



