#!/bin/bash
# This is a not very nice bash script to do some kind
# of naive functional testing for ai-add-param

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
IN=$(mktemp)
TESTNODE="aifcliftest99.cern.ch"

cat > $CONF << EOF
[foreman]
foreman_hostname = ${FOREMAN_HOSTNAME}
foreman_port = 8443
foreman_timeout = 60

EOF

echo 'Running tests with foreman configuration:'
cat $CONF

_expect 0 ai-add-param --config $CONF --hg playground/aitoolstest foo bar
_expect 0 ai-add-param --config $CONF --hg playground/aitoolstest foo bar
_expect 0 ai-add-param --config $CONF --hg playground/aitoolstest foo bar2


echo "$TESTNODE 192.168.0.1 aa:bb:cc:dd:ee:ff" >> $IN
_expect 0 ai-foreman --config $CONF addhost -c playground/aitoolstest -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN

_expect 0 ai-add-param --config $CONF $TESTNODE foo2 bar2
_expect 5 ai-add-param --config $CONF $TESTNODE foo2 bar2
_expect 5 ai-add-param --config $CONF $TESTNODE foo2 bar3

echo "Tearing down..."
_expect 0 ai-foreman --config $CONF delhost $TESTNODE
rm -f $CONF
echo "All tests passed :)"
