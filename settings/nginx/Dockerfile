FROM nginx:latest

RUN apt-get update && mkdir -pv /srv/ww4/context/ && mkdir -pv /srv/ww4/projects &&  mkdir -pv /srv/ww4/api
COPY . /srv/ww4/api
COPY cors.filter /etc/nginx/cors.filter
COPY nginx.conf /etc/nginx/nginx.conf
COPY mime.types /etc/nginx/mime.types