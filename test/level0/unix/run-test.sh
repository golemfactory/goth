#!/bin/bash
#
#  Level 0 Test Scenario
#

log() {
    echo -e "\e[45m>>>        ${1}        <<<\e[0m"
}

log "Starting Mk1 Net Hub" && ./start_net_mk1_hub.sh &
HUB_PID=$!
sleep 3

log "Starting provider daemon" && ./with_env.sh provider.env start_daemon.sh &
PROV_DAEMON_PID=$!
sleep 3

log "Starting requestor daemon" && ./with_env.sh requestor.env start_daemon.sh &
REQ_DAEMON_PID=$!
sleep 3

log "Starting provider agent" && ./start_provider.sh &
PROV_AGENT_PID=$!
sleep 3

log "Starting requestor agent" && ./start_requestor.sh &
REQ_AGENT_PID=$!
sleep 5


cleanup() {
    [ -z "$REQ_AGENT_PID" ] || kill "$REQ_AGENT_PID"
    [ -z "$PROV_AGENT_PID" ] || kill "$PROV_AGENT_PID"
    [ -z "$REQ_DAEMON_PID" ] || kill "$REQ_DAEMON_PID"
    [ -z "$PROV_DAEMON_PID" ] || kill "$PROV_DAEMON_PID"
    [ -z "HUB_PID" ] || kill "$HUB_PID"
    log "Cleaned up"
    exit 0
}    

trap cleanup SIGINT

while true; do
    log "Press CTRL+C to stop the test"
    sleep 3
done
