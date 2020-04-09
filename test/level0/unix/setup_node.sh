# This script (re)creates the data directory used for the yagna daemon,
# runs the daemon, creates an app key and stops the daemon.
#
# Network hub must be running on $CENTRAL_NET_HOST.

# Create data directory
[ ! -e "$DATA_DIR" ] || rm -r "$DATA_DIR"
mkdir "$DATA_DIR"

# Start the yagna daemon in the background
DAEMON_LOG=$(mktemp -p . "daemon_XXXX.log")
sh ./start_daemon.sh 2> $DAEMON_LOG &

# Observe daemon's stderr
tail -f $DAEMON_LOG > /dev/stderr &
trap "kill $!" EXIT

# Wait until the daemon is ready to create keys
tail -f $DAEMON_LOG | grep -m1 'Market service successfully activated'

# Create app key
yagna app-key drop "$KEY_NAME"
yagna app-key create "$KEY_NAME"

# Stop the daemon
sh ./stop_daemon.sh
rm -f $DAEMON_LOG
