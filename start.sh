#!/bin/bash

/usr/bin/uwsgi -s /tmp/civilwars.sock --manage-script-name --mount /var/www/dnd.romanh.de=app