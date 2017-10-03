#!/usr/bin/env bash

# This is used to flush out all migrations, flasharray tables, etc.
# Note: you will lose all of your flasharray monitoring data.
reset_db () {
    echo "Fetching MySQL table names."
    tables=`mysql -u root -p -e "use flash_stache; show tables;" | grep "flasharray"`
    echo "Deleting tables: ${tables}."
    sqlcmd="SET FOREIGN_KEY_CHECKS=0; USE flash_stache; DELETE FROM django_migrations WHERE app = 'flasharray';"
    for table in ${tables};
        do sqlcmd+="drop table ${table};";
    done
    mysql -u root -p -e "${sqlcmd}"
    rm -f flasharray/migrations/0*.py  # Assumes that migrations won't start with anything but 0.
};

while true; do
    read -p "Are you sure that you want to reset FlashStache databases?" yesno
    case $yesno in
        [Yy]* ) reset_db; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
