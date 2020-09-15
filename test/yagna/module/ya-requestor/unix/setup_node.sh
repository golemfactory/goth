# This script (re)creates the data directory used for the yagna daemon,
# runs the daemon, creates an app key and stops the daemon.
#
# Network hub must be running on $CENTRAL_NET_HOST.

echo "Create data directory"
[[ ! -e "$DATA_DIR" ]] || rm -r "$DATA_DIR"
mkdir "$DATA_DIR"

echo "Start the yagna daemon in the background"
if [[ "$OSTYPE" = "darwin"* ]]; then
  DAEMON_LOG=$(mktemp -t "./daemon_XXXX.log")
else
  DAEMON_LOG=$(mktemp -p . "daemon_XXXX.log")
fi
sh ./start_daemon.sh 2> $DAEMON_LOG &

echo "Observe daemon's stderr"
tail -f $DAEMON_LOG > /dev/stderr &
trap "kill $!" EXIT

echo "Wait until the daemon is ready to create keys"
tail -f $DAEMON_LOG | grep -m1 'Market service successfully activated'

DEFAULT_KEY=$(sh get_node_id.sh)
echo "Default key=${DEFAULT_KEY}"

echo "Creating key from keystore ${YAGNA_KEY_FILE}"
CREATE_KEY_RESULT=$(yagna id create --json --no-password --from-keystore ${YAGNA_KEY_FILE})
echo "Create key completed, result=${CREATE_KEY_RESULT}"

echo "Setting created key as default"
SCRIPT="\
import json, sys; \
j = json.load(sys.stdin); \
print(j['Ok']['nodeId'])"
NEW_KEY=$(echo ${CREATE_KEY_RESULT} | python3 -c "${SCRIPT}")
yagna id update --set-default "${NEW_KEY}"

echo "Dropping old key ${DEFAULT_KEY}"
yagna id drop ${DEFAULT_KEY}

echo "Create app key"
yagna app-key drop "$KEY_NAME"
yagna app-key create "$KEY_NAME"

echo "Stop the daemon"
sh ./stop_daemon.sh
rm -f $DAEMON_LOG
