# install the epel-release distro info, and update it.
sudo yum -y install epel-release
sudo yum -y update

# Install git, because we need that shit.
sudo yum -y install git

# Needed for some installations in pip, like uwsgi, since it doesn't have a compiler.
sudo yum -y groupinstall "Development Tools"

# Install redis and start it.
sudo yum -y install redis
sudo systemctl start redis
sudo systemctl enable redis

# Install and configure mariadb server
sudo yum -y install mariadb-server
sudo yum -y install mysql-devel
sudo systemctl enable mariadb
sudo systemctl start mariadb

firewall-cmd --permanent --zone=public --add-port=3000/tcp
firewall-cmd --permanent --zone=public --add-port=3306/tcp

sudo yum -y install expect

# Configure root password for mariadb
MYSQL_INSTALL=$(expect -c "
set timeout 10
spawn mysql_secure_installation
expect \"Enter current password for root (enter for none):\"
send \"\r\"
expect \"Set root password?\"
send \"\r\"
expect \"New password:\"
send \"${password}\r\"
expect \"Re-enter new password:\"
send \"${password}\r\"
expect \"Remove anonymous users?\"
send \"\r\"
expect \"Disallow root login remotely?\"
send \"\r\"
expect \"Remove test database and access to it?\"
send \"\r\"
expect \"Reload privilege tables now?\"
send \"\r\"
expect eof
")
echo "$MYSQL_INSTALL"

sudo systemctl restart mariadb

# This is with the root password blank:
/usr/bin/mysql -h 0.0.0.0 -P 3306 --protocol=tcp -u root --password=${password} -e "CREATE DATABASE IF NOT EXISTS flash_stache; SET @@global.time_zone = '+00:00';"

# Install pip from source
git clone https://github.com/pypa/pip.git
cd pip
python ./setup.py install
cd -

# Install pip libraries
pip install django django-multiselectfield django-rq django-rq-scheduler grafana_api_client MySQL-python purestorage uwsgi

# Install grafana
sudo yum -y install https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana-4.6.2-1.x86_64.rpm
# from FlashStache repo directory
yes | cp flasharray/static/js/flash_stache.js /usr/share/grafana/public/dashboards/
yes | cp flasharray/static/image/mustache.png  /usr/share/grafana/public/img/fav32.png
yes | cp flasharray/static/image/mustache.svg /usr/share/grafana/public/img/grafana_icon.svg
yes | cp defaults.ini /usr/share/grafana/conf/defaults.ini
for file in `ls /usr/share/grafana/public/css/*`; do echo $file; /bin/sed -i 's/\\e903/FlashStache/g' ${file}; done
service grafana-server start

# # Give the grafana-server time to start
# sleep 5
# python configure_grafana.py -p ${password} &>> ./install.log || stop_install
# /bin/systemctl enable grafana-server &>> ./install.log || stop_install
#
# echo -e  "\nStep 5: Starting and configuring web services."
# echo -e "\t- Configuring Web Server and Dependencies"
#
# # Update password in the django database settings:
# sed -i "s/'PASSWORD':\ 'changeme'\,/'PASSWORD':\ '${password}'\,/g" flash_stache/settings.py  &>> ./install.log || stop_install
# python manage.py makemigrations &>> ./install.log || stop_install
# python manage.py migrate &>> ./install.log || stop_install
# echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@flash_stache.com', '${password}')" | /usr/bin/python manage.py shell &>> ./install.log
# service grafana-server restart  &>> ./install.log || stop_install
#
# # Configure WSGI (nginx)
# echo -e "\t- Configuring Nginx"
# ufw allow 8080  &>> ./install.log || stop_install
# mkdir -p /etc/uwsgi/sites  &>> ./install.log || stop_install
# sed -i "s/change_me/${ip_addr}/g" flash_stache/flash_stache  &>> ./install.log || stop_install
# sed -i "s/path_to_change/${curdir//\//\\/}\/flasharray/g" flash_stache/flash_stache  &>> ./install.log || stop_install
# sed -i "s/change_me/${user}/g" flash_stache/uwsgi.service  &>> ./install.log || stop_install
# sed -i "s/change_me/${user}/g" flash_stache/flash_stache.ini  &>> ./install.log || stop_install
# sed -i "s/change_path/${curdir//\//\\/}/g" flash_stache/flash_stache.ini &>> ./install.log || stop_install
# cp flash_stache/flash_stache.ini /etc/uwsgi/sites/flash_stache.ini  &>> ./install.log || stop_install
# cp flash_stache/uwsgi.service /etc/systemd/system/uwsgi.service  &>> ./install.log || stop_install
#
# apt-get install -y nginx  &>> ./install.log || stop_install
#
# ln -s /etc/nginx/sites-available/flash_stache /etc/nginx/sites-enabled  &>> ./install.log || stop_install
# cp flash_stache/flash_stache /etc/nginx/sites-available/  &>> ./install.log || stop_install
# nginx -t  &>> ./install.log || stop_install
# echo -e "\t- Starting Nginx"
# # uwsgi --http :8080 --chdir ${curdir}/flash_stache/ -w flash_stache.wsgi &>> ./install.log || stop_install
# echo -e "\t- Configuring boot time settings"
# systemctl restart nginx  &>> ./install.log || stop_install
# systemctl start uwsgi  &>> ./install.log || stop_install
#
# # Now close the port and enable Nginx in the firewall rules
# ufw delete allow 8080  &>> ./install.log || stop_install
# ufw allow 'Nginx Full'  &>> ./install.log || stop_install
# systemctl enable nginx  &>> ./install.log || stop_install
# systemctl enable uwsgi  &>> ./install.log || stop_install
#
# # Workaround for a bug in Nginx:
# cp flash_stache/proxy_params /etc/nginx/proxy_params &>> ./install.log || stop_install
# systemctl restart nginx  &>> ./install.log || stop_install
# systemctl restart uwsgi &>> ./install.log || stop_install
#
# echo -e "\t- Starting services and worker tasks"
# ./start.sh &>> ./install.log || stop_install
