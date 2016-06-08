#!/bin/bash

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
TESTNODE="aifcliftest99.cern.ch"
cat > $CONF << EOF
[foreman]
foreman_hostname = ${FOREMAN_HOSTNAME}
foreman_port = 8443
foreman_timeout = 60

[landb]
landb_hostname = network.cern.ch
landb_port = 443

[roger]
roger_hostname = woger.cern.ch
roger_port = 8201
roger_timeout = 15

[aidisownhost]
owner = sysadmin-team
hostgroup = retirement/incoming
EOF
IN=$(mktemp)

echo "$TESTNODE 192.168.0.1 aa:bb:cc:dd:ee:ff" >> $IN

_expect 0 ai-foreman --config $CONF addhost -c playground/aitoolstest/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN

echo "Arguments..."
_expect 2 ai-disownhost --config $CONF

echo "Disown..."
# Will fail as the host does not exist and cannot be fqdnified.
_expect 1 ai-disownhost --config $CONF --roger-disable --landb-disable --landb-pass foo $TESTNODE

echo "Tearing down..."
_expect 0 ai-foreman --config $CONF delhost $TESTNODE
rm -rf $IN $CONF
echo "All tests passed :)"
