FROM ubuntu:22.04

RUN apt update \
    && apt install -y libssl-dev ca-certificates \
    && update-ca-certificates \
    && apt install -y ncat iperf3

RUN printf '#!/bin/bash \n\
ncat -e /bin/cat -k -l 22235 & \n\
ncat -l 22236 -k >/dev/null & \n\
iperf3 -p 22237 -s & \n\
while true; do sleep 1; done' >> /usr/bin/entrypoint.sh

RUN chmod +x /usr/bin/entrypoint.sh

ENTRYPOINT /usr/bin/entrypoint.sh