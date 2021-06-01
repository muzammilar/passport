ssh passport-priv.ccs.neu.edu
sudo su passport
cd ~/passport-online-system/geoloc-server/
source ../pp-env/bin/activate
pkill -9 uwsgi
git reset --hard
git pull
scp ../../config.txt .
scp ../../config.py .
uwsgi --enable-threads --python geoloc_server.py &

