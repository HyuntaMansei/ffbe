CREATE USER 'ffbeuser'@'%' IDENTIFIED BY 'leonis';
GRANT SELECT ON ffbe.* TO 'ffbeuser'@'%';
FLUSH PRIVILEGES;