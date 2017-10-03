# FlashStache

* Comes with several template dashboards
* Additional dashboards can be created in Grafana
* To start required services run start.sh
    * MySQL/Django/Grafana will start on boot

# Recommendations:

* 4+ CPU Cores
* 4+ GB of RAM
* 5+ GB of storage per FlashArray (per 24 hours of retention)
* For the IP Address, use a virtual interface (such as vir0)
* For the API Token, use read-only user (Pure Storage read-only AD group)


# Future:

* Scale out workers to support more arrays (tested with up to 10)
* Scale out database/webserver/logging/etc. for better performance
* Improved User Authentication/security (currently only has an admin user)
* Simplify new dashboard template importing
* Additional dashboards (pre-built) upon request
* Automate redis workers spawning on reboot
    * Possibly change to use Celery w/ Supervisor

# Installation (Ubuntu 16.04):

* Clone/pull the repository
* Run the setup.sh
* Add FlashArrays for monitoring
