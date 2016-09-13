#!/bin/bash
# This is a not very nice bash script to do some kind
# of naive functional testing for ai-ipmi

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
IN=$(mktemp)
MAC="dd:ee:ff:aa:bb:cc"
TESTNODE="aifcliftest99.cern.ch"
TESTNODE_IPMI="aifcliftest99-ipmi.cern.ch"

cat > $CONF << EOF
[foreman]
foreman_hostname = ${FOREMAN_HOSTNAME}
foreman_port = 8443
foreman_timeout = 60

EOF

echo 'Running tests with foreman configuration:'
cat $CONF

echo "$TESTNODE 192.168.0.1 aa:bb:cc:dd:ee:ff" >> $IN
_expect 0 ai-foreman --config $CONF addhost -c playground/aitoolstest -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN
_expect 0 ai-ipmi --config $CONF add-ipmi $TESTNODE $TESTNODE_IPMI $MAC foo bar -i 192.168.1.1
#_expect 0 ai-ipmi --config $CONF get-creds $TESTNODE
_expect 0 ai-ipmi --config $CONF change-ipmi-creds $TESTNODE --user foo2 --pw bar2
#_expect 0 ai-ipmi --config $CONF get-creds $TESTNODE

echo "Tearing down..."
_expect 0 ai-foreman --config $CONF delhost $TESTNODE
rm -f $CONF
echo "All tests passed :)"
