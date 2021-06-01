#! /bin/bash
sudo yum install mariadb-server mariadb -y
sudo yum -y install gcc gcc-c++ numpy python-devel scipy
sudo yum install mysql-devel -y
sudo yum install MySQL-python -y
sudo yum install python-pip -y
sudo pip install django==1.4 -y
sudo pip install virtualenv -y
sudo pip install shapely[vectorized]==1.6b2
sudo yum install git -y
sudo yum install traceroute -y
sudo yum groupinstall 'Development Tools' -y
sudo yum install gcc-gfortran -y
sudo yum install python-devel -y
sudo yum install atlas-devel -y
sudo yum install graphviz -y
sudo yum install https://download1.rpmfusion.org/free/el/rpmfusion-free-release-7.noarch.rpm -y
sudo yum install geos-3.4.2 -y
sudo yum install geos-devel -y
sudo yum install openssl-devel -y
sudo yum install libffi-devel -y
sudo yum install -y nginx zlib-devel sqlite-devel bzip2-devel
sudo yum install tkinter -y




