CREATE USER 'ffbeuser'@'%' IDENTIFIED BY 'leonis';
GRANT SELECT, INSERT ON ffbe.* TO 'ffbeuser'@'%';
GRANT SELECT, INSERT ON database_name.table_name TO 'example_user'@'localhost';
FLUSH PRIVILEGES;

SHOW GRANTS FOR 'ffbeuser'@'%';

CREATE USER 'ffbemaster'@'%' IDENTIFIED BY 'aksaksgo1!';
GRANT ALL PRIVILEGES ON ffbe.* TO 'ffbemaster'@'%' WITH GRANT OPTION;

SHOW GRANTS FOR 'ffbemaster'@'%';

show processlist;
KILL 51305;