#!/bin/bash
# This is a not very nice bash script to do some kind
# of naive functional testing for ai-bs-vm.

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
cat > $CONF << EOF
[DEFAULT]
dereference_alias = true

[foreman]
foreman_hostname = ${FOREMAN_HOSTNAME}
foreman_port = 8443
foreman_timeout = 60

[pdb]
pdb_hostname = constable.cern.ch
pdb_port = 9081
pdb_timeout = 15

[enc]
enc_hostname = ${FOREMAN_HOSTNAME}
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

IMAGE='9f215a0d-91bd-4213-bd15-c426e29a0b3b'

PUPPETINIT="$(dirname '$0')/../userdata/puppetinit"

echo "Testing incorrect combinations..."
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --slc5 --slc6
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --slc5 --cc7
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --slc6 --cc7
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --slc5 --slc6 --c7

_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest -i "$IMAGE" --slc5
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest -i "$IMAGE" --slc6
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest -i "$IMAGE" --cc7

_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --nova-boot-from-new-volume '1GB' -i "$IMAGE" --slc5
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --nova-boot-from-new-volume '1GB' -i "$IMAGE" --slc6
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --nova-boot-from-new-volume '1GB' -i "$IMAGE" --cc7
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --slc5 --nova-boot-from-existing-volume '0207a0b8-9e72-42bd-ae10-5bd6df454fd1'
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --slc6 --nova-boot-from-existing-volume '0207a0b8-9e72-42bd-ae10-5bd6df454fd1'
_expect 2 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -g playground/aitoolstest --cc7 --nova-boot-from-existing-volume '0207a0b8-9e72-42bd-ae10-5bd6df454fd1'


echo "Checking valid combinations..."
_expect 0 ai-bs-vm --config $CONF --puppetinit-path $PUPPETINIT -d -g playground/aitoolstest --slc5
_expect 0 ai-bs-vm --config $CONF --puppetinit-path $PUPPETINIT -d -g playground/aitoolstest --slc6
_expect 0 ai-bs-vm --config $CONF --puppetinit-path $PUPPETINIT -d -g playground/aitoolstest --cc7
_expect 0 ai-bs-vm --config $CONF --puppetinit-path $PUPPETINIT -d -g playground/aitoolstest --slc5 --nova-boot-from-new-volume '10GB'
_expect 0 ai-bs-vm --config $CONF --puppetinit-path $PUPPETINIT -d -g playground/aitoolstest --slc6 --nova-boot-from-new-volume '10GB:delete-on-terminate'
_expect 0 ai-bs-vm --config $CONF --puppetinit-path $PUPPETINIT -d -g playground/aitoolstest --cc7 --nova-boot-from-new-volume '10GB:type=cp1'
_expect 0 ai-bs-vm --config $CONF --puppetinit-path $PUPPETINIT -d -g playground/aitoolstest --slc5 --nova-boot-from-new-volume '10GB' --nova-attach-new-volume 'vdb=1GB' --nova-attach-new-volume 'vdc=1GB'
_expect 0 ai-bs-vm --config $CONF --puppetinit-path $PUPPETINIT -d -g playground/aitoolstest --slc6 --nova-attach-new-volume 'vdb=1GB:delete-on-terminate' --nova-attach-new-volume 'auto=1GB:type=cp1' --nova-attach-new-volume 'vdd=1GB:delete-on-terminate:type=io1'


echo "Userdata dump..."
#_expect 7 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest -i "$IMAGE" --userdata-dump /etc/passwd
DUMP=$(mktemp -u)
_expect 0 ai-bs-vm --puppetinit-path $PUPPETINIT --config $CONF -d -g playground/aitoolstest -i "$IMAGE" --userdata-dump $DUMP
_expect 0 test -s $DUMP
rm -rf $DUMP

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
