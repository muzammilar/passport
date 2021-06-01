# my sql
wget https://dev.mysql.com/get/mysql57-community-release-el7-9.noarch.rpm
sudo rpm -ivh mysql57-community-release-el7-9.noarch.rpm
sudo yum install mysql-server -y
sudo systemctl start mysqld
sudo systemctl status mysqld
sudo grep 'temporary password' /var/log/mysqld.log
sudo mysql_secure_installation
mysqladmin -u root -p version
