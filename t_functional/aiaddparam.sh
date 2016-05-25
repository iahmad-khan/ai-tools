#!/bin/bash
# This is a not very nice bash script to do some kind
# of naive functional testing for ai-add-param

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
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
_expect 0 ai-add-param --config $CONF nachodev03.cern.ch foo2 bar2
_expect 0 ai-add-param --config $CONF nachodev03.cern.ch foo2 bar2
_expect 0 ai-add-param --config $CONF nachodev03.cern.ch foo2 bar3

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
