FROM ghcr.io/golemfactory/goth/yagna-outbound-base:1.0.0

RUN update-ca-certificates

RUN printf '#!/bin/bash \n\
ncat -e /bin/cat -k -l 22235 & \n\
ncat -l 22236 -k >/dev/null & \n\
iperf3 -p 22237 -s & \n\
while true; do sleep 1; done' >> /usr/bin/entrypoint.sh

RUN chmod +x /usr/bin/entrypoint.sh

ENTRYPOINT /usr/bin/entrypoint.sh