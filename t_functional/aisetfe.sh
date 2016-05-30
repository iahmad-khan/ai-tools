#!/bin/bash
source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
cat > $CONF << EOF
[foreman]
foreman_hostname = ${FOREMAN_HOSTNAME}
foreman_port = 8443
foreman_timeout = 60
EOF

FECACHE=$(mktemp)
cat > $FECACHE << EOF
{"Configuration Management": "Imfake"}
EOF

_expect 0 ai-set-fe --config $CONF --fecache $FECACHE --hostgroup playground/aitoolstest \"Configuration Management\"
_expect 3 ai-set-fe --config $CONF --fecache $FECACHE --hostgroup playground/aitoolstest \"This will never exist\"
_expect 0 ai-set-fe --config $CONF --fecache $FECACHE --hostgroup playground/aitoolstest Ignore
_expect 4 ai-set-fe --config $CONF --fecache $FECACHE --hostgroup hope/this/will/never/exist Ignore

echo "Tearing down..."
rm -f $CONF $FECACHE
echo "All tests passed :)"
