FROM nginx:1.19

COPY goth/api_monitor/nginx.conf /etc/nginx/nginx.conf

COPY goth/address.py /root/address.py

SHELL ["/bin/bash", "-c"]

# This will read from /root/address.py definitions of the form:
#
#   VAR = N
#
# where VAR includes "_PORT" and N is a 4- or 5-digit number,
# and replace each {VAR} in nginx.conf with N:

RUN  grep -P '^([A-Z_]*_PORT[A-Z_]*)\s*=\s*([0-9]){4,5}$' /root/address.py \
     | while IFS=$' \t=' read VAR VALUE; do \
         sed -i "s/{$VAR}/$VALUE/g" /etc/nginx/nginx.conf;\
     done

RUN a=`getent hosts host.docker.internal | awk '{ print $1 }'` \
    && [[ -n "$a" ]] && HOST_ADDR=$a || HOST_ADDR="172.19.0.1" \
    && sed -i "s/{HOST_ADDR}/$HOST_ADDR/" /etc/nginx/nginx.conf
