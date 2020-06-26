FROM nginx:1.19

COPY goth/api_monitor/nginx.conf /etc/nginx/nginx.conf
