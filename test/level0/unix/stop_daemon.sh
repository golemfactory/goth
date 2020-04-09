# Do your best to stop a yagna daemon.
# In case multiple daemons are running, the one to be stopped
# is identified by the $DATA_DIR it uses.
DAEMON_PID=$(ps a \
		 | grep "yagna service run -d $DATA_DIR" \
		 | grep -v "grep" | \
		 sed 's/^ *\([0-9]\+\).*/\1/')
if [ -z "$DAEMON_PID" ]; then
    echo "Cannot find a running yagna process that uses \"$DATA_DIR\"" > /dev/stderr
else
    kill -9 "$DAEMON_PID"
fi

