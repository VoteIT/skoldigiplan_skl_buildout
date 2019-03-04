#!/bin/bash
#Ment to be run as root after buildout is done. Will obtain cert and install on nginx debian

cd /etc/nginx
ln -s /home/voteit/srv/skoldigiplan_skl_buildout/etc/nginx.conf ./sites-available/skoldigiplan-skl.conf
ln -s ./sites-available/skoldigiplan-skl.conf ./sites-enabled/.

service nginx stop
certbot certonly --standalone -d skoldigiplan-skl.voteit.se
service nginx start
