#!/bin/bash
# This is a not very nice bash script to do some kind
# of naive functional testing for ai-bs-vm.

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
cat > $CONF << EOF
[DEFAULT]
dereference_alias = true

[foreman]
foreman_hostname = judy.cern.ch
foreman_port = 8443
foreman_timeout = 60

[pdb]
pdb_hostname = judy.cern.ch
pdb_port = 9081
pdb_timeout = 15

[enc]
enc_hostname = judy.cern.ch
enc_port = 8443
enc_timeout = 15

[roger]
roger_hostname = woger.cern.ch
roger_port = 8201
roger_timeout = 15

[certmgr]
certmgr_hostname = baby02.cern.ch
certmgr_port = 8008
certmgr_timeout = 15

[tbag]
tbag_hostname = woger.cern.ch
tbag_port = 8201
tbag_timeout = 15

[nova]
nova_timeout = 45
EOF

PUPPETINIT="$(dirname '$0')/../userdata/puppetinit"

echo "Testing valid FQDNs..."
_expect 0 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7
_expect 0 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 foo
_expect 0 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 foo.cern.ch
_expect 0 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 foo.bar.cern.ch
_expect 0 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 foo.bar.baz.cern.ch
_expect 0 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 "$(printf 'a%.0s' {1..63}).cern.ch"

echo "Testing incorrect combinations..."
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -i foo

echo "Testing invalid FQDNs..."
_expect 5 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 foo.bar
_expect 5 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 foo.bar.com
_expect 5 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 foo..cern.ch
_expect 5 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest --cc7 .cern.ch
_expect 5 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g \
    playground/aitoolstest --cc7 "$(printf 'a%.0s' {1..60}).$(printf 'a%.0s' {1..64})cern.ch"
_expect 5 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g \
    playground/aitoolstest --cc7 "$(printf 'a%.0s' {1..64}).cern.ch"
_expect 5 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g \
    playground/aitoolstest --cc7 \
    "$(printf 'a%.0s' {1..63}).$(printf 'a%.0s' {1..63}).$(printf 'a%.0s' {1..63}).$(printf 'a%.0s' {1..63}).cern.ch"

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
