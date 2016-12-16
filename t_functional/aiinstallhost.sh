#!/bin/bash
# This is a not very nice bash script to do some kind
# of naive functional testing for ai-installhost.

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
cat > $CONF << EOF
[foreman]
foreman_hostname = ${FOREMAN_HOSTNAME}
foreman_port = 8443
foreman_timeout = 60

[roger]
roger_hostname = woger.cern.ch
roger_port = 8201
roger_timeout = 15

[certmgr]
certmgr_hostname = baby02.cern.ch
certmgr_port = 8008
certmgr_timeout = 15
EOF
IN=$(mktemp)

echo "Setting up..."

echo "Arguments"
_expect 2 ai-installhost --config $CONF
_expect 2 ai-installhost --config $CONF -d wonteverexist444.cern.ch --mode fail

# Basically to test parameters :/
echo "Installhost..."
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --console ttyS0
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch -k -a
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch -r
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --report-to someuser
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --mode auto
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --mode uefi
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --mode arm64
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --mode bios
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --mode bioslgcy
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --aims-target FOO

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
