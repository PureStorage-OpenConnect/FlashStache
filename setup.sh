#!/usr/bin/env bash

curdir=`pwd`
ip_addr=`hostname -I`
user=`who am i | awk '{print $1}'`

# Confirm root user / sudo
if (( $EUID != 0 )); then
    echo -e "Please run as root.\n'sudo -H' is recommended."
    exit
fi


stop_install () {
    echo "Installation failed.  See install.log for more information.";
    # Stop the parent script
    kill -9 `ps --pid $$ -oppid=`; exit
};

echo -e "\nInstalling FlashStache: (This will take several minutes)\n- Please don't interrupt -\n"

# Configure the admin password:
while true; do
    read -s -p "Please set a password for the Admin role: " password
    echo
    read -s -p "Confirm password: " password2
    echo
    [ "${password}" = "${password2}" ] && break
    echo "Passwords did not match."
done
echo "Admin Password Set."

# Begin Installation:
echo -e  "\nStep 1: Installing dependencies."
echo -e "\t- Updating Ubuntu"
apt-get update -y &> ./install.log || stop_install
apt-get upgrade -y &>> ./install.log || stop_install
echo -e "\t- Installing Python, MySQL client, Redis, etc."
apt-get install -y python-pip python-dev redis-server libmysqlclient-dev wget adduser libfontconfig &>> ./install.log || stop_install
apt install -y expect python &>> ./install.log || stop_install

echo -e  "\nStep 2: Installing Python modules."
pip2 install --upgrade pip &>> ./install.log || stop_install
pip2 install django==1.11 &>> ./install.log || stop_install
pip2 install django-multiselectfield==0.1.8 &>> ./install.log || stop_install
pip2 install django-rq==1.0.1 &>> ./install.log || stop_install
pip2 install django-rq-scheduler==1.1.1 &>> ./install.log || stop_install
pip2 install grafana_api_client==0.2.0 &>> ./install.log || stop_install
pip2 install MySQL-python==1.2.5 &>> ./install.log || stop_install
pip2 install purestorage==1.11.3 &>> ./install.log || stop_install
pip2 install uwsgi==2.0.16 &>> ./install.log || stop_install
pip2 install requests==2.18.4  &>> ./install.log || stop_install


echo -e  "\nStep 3: Starting and configuring MySQL Server."
MYSQL_INSTALL=$(expect -c "

set timeout 10
spawn apt-get install -y mysql-server

expect \"New password for the MySQL "root" user:\"
send \"${password}\r\"
expect \"Repeat password for the MySQL "root" user:\"
send \"${password}\r\"

expect eof
")


echo "$MYSQL_INSTALL" &>> ./install.log || stop_install
service mysql start &>> ./install.log || stop_install
# Give mysql some time to start
sleep 10;
/usr/bin/mysql -h 0.0.0.0 -P 3306 --protocol=tcp -u root --password=${password} -e "CREATE DATABASE IF NOT EXISTS flash_stache; SET @@global.time_zone = '+00:00';" &>> ./install.log || stop_install

echo -e  "\nStep 4: Starting and configuring Grafana Server."
echo -e "\t- Downloading Grafana dpkg."
wget -nc https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana_4.5.2_amd64.deb &>> ./install.log || stop_install
# Sleep for 5 seconds so we don't have lock contention for the dpkg file.
sleep 5;
echo -e "\t- Installing Grafana"
lsof /var/lib/dpkg/lock
dpkg -i ./grafana_4.5.2_amd64.deb || stop_install  # TODO: Figure out why this breaks when redirected...
echo -e "\t- Configuring Grafana and starting Services"
cp flasharray/static/js/flash_stache.js /usr/share/grafana/public/dashboards/ &>> ./install.log || stop_install
cp flasharray/static/image/mustache.png  /usr/share/grafana/public/img/fav32.png &>> ./install.log || stop_install
cp flasharray/static/image/mustache.svg /usr/share/grafana/public/img/grafana_icon.svg &>> ./install.log || stop_install
cp defaults.ini /usr/share/grafana/conf/defaults.ini &>> ./install.log || stop_install
for file in `ls /usr/share/grafana/public/css/*`; do echo $file; /bin/sed -i 's/\\e903/FlashStache/g' ${file}; done &>> ./install.log || stop_install
service grafana-server start &>> ./install.log || stop_install
# Give the grafana-server time to start
sleep 5
python configure_grafana.py -p ${password} &>> ./install.log || stop_install
/bin/systemctl enable grafana-server &>> ./install.log || stop_install

echo -e  "\nStep 5: Starting and configuring web services."
echo -e "\t- Configuring Web Server and Dependencies"
# Update password in the django database settings:
sed -i "s/'PASSWORD':\ 'changeme'\,/'PASSWORD':\ '${password}'\,/g" flash_stache/settings.py  &>> ./install.log || stop_install
python manage.py makemigrations &>> ./install.log || stop_install
python manage.py migrate &>> ./install.log || stop_install
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@flash_stache.com', '${password}')" | /usr/bin/python manage.py shell &>> ./install.log
service grafana-server restart  &>> ./install.log || stop_install

# Configure WSGI (nginx)
echo -e "\t- Configuring Nginx"
ufw allow 8080  &>> ./install.log || stop_install
mkdir -p /etc/uwsgi/sites  &>> ./install.log || stop_install
sed -i "s/change_me/${ip_addr}/g" flash_stache/flash_stache  &>> ./install.log || stop_install
sed -i "s/path_to_change/${curdir//\//\\/}\/flasharray/g" flash_stache/flash_stache  &>> ./install.log || stop_install
sed -i "s/change_me/${user}/g" flash_stache/uwsgi.service  &>> ./install.log || stop_install
sed -i "s/change_me/${user}/g" flash_stache/flash_stache.ini  &>> ./install.log || stop_install
sed -i "s/change_path/${curdir//\//\\/}/g" flash_stache/flash_stache.ini &>> ./install.log || stop_install
cp flash_stache/flash_stache.ini /etc/uwsgi/sites/flash_stache.ini  &>> ./install.log || stop_install
cp flash_stache/uwsgi.service /etc/systemd/system/uwsgi.service  &>> ./install.log || stop_install

apt-get install -y nginx  &>> ./install.log || stop_install

ln -s /etc/nginx/sites-available/flash_stache /etc/nginx/sites-enabled  &>> ./install.log || stop_install
cp flash_stache/flash_stache /etc/nginx/sites-available/  &>> ./install.log || stop_install
nginx -t  &>> ./install.log || stop_install
echo -e "\t- Starting Nginx"
# uwsgi --http :8080 --chdir ${curdir}/flash_stache/ -w flash_stache.wsgi &>> ./install.log || stop_install
echo -e "\t- Configuring boot time settings"
systemctl restart nginx  &>> ./install.log || stop_install
systemctl start uwsgi  &>> ./install.log || stop_install

# Now close the port and enable Nginx in the firewall rules
ufw delete allow 8080  &>> ./install.log || stop_install
ufw allow 'Nginx Full'  &>> ./install.log || stop_install
systemctl enable nginx  &>> ./install.log || stop_install
systemctl enable uwsgi  &>> ./install.log || stop_install

# Workaround for a bug in Nginx:
cp flash_stache/proxy_params /etc/nginx/proxy_params &>> ./install.log || stop_install
systemctl restart nginx  &>> ./install.log || stop_install
systemctl restart uwsgi &>> ./install.log || stop_install

echo -e "\t- Starting services and worker tasks"
./start.sh &>> ./install.log || stop_install
