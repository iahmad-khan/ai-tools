# This is a not very nice bash script to do some kind
# of naive functional testing for ai-bs-vm.

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

function _expect {
  ret=$1
  shift
  cmd=$*
  eval $cmd
  if [ $ret -ne $? ]
  then
    echo "$cmd didn't return the expected return code ($ret)"
    exit
  fi
}

IMAGE='9f215a0d-91bd-4213-bd15-c426e29a0b3b'


echo "Testing incorrect combinations..."
_expect 2 ai-bs-vm -g playground/aitoolstest
_expect 2 ai-bs-vm -g playground/aitoolstest -i "$IMAGE" --nova-boot-from-existing-volume '0207a0b8-9e72-42bd-ae10-5bd6df454fd1'
_expect 2 ai-bs-vm -g playground/aitoolstest --nova-boot-from-new-volume '1GB'
_expect 2 ai-bs-vm -g playground/aitoolstest --nova-boot-from-new-volume '1GB' --nova-boot-from-existing-volume '0207a0b8-9e72-42bd-ae10-5bd6df454fd1'

echo "Testing wrong values..."
_expect 2 ai-bs-vm -g playground/aitoolstest --nova-boot-from-existing-volume 'no UUID!'
_expect 2 ai-bs-vm -g playground/aitoolstest --nova-boot-from-new-volume 'wrongsize'
_expect 2 ai-bs-vm -g playground/aitoolstest -i "$IMAGE" --nova-attach-new-volume 'devicemissing'
_expect 2 ai-bs-vm -g playground/aitoolstest -i "$IMAGE" --nova-attach-new-volume 'vdb=noSize'
_expect 2 ai-bs-vm -g playground/aitoolstest -i "$IMAGE" --nova-attach-new-volume 'vdb=1GB:wrong-flag'
_expect 2 ai-bs-vm -g playground/aitoolstest -i "$IMAGE" --nova-attach-existing-volume 'devicemissing'
_expect 2 ai-bs-vm -g playground/aitoolstest -i "$IMAGE" --nova-attach-existing-volume 'vdb=noUUID'
_expect 2 ai-bs-vm -g playground/aitoolstest -i "$IMAGE" --nova-attach-existing-volume 'vdb=0207a0b8-9e72-42bd-ae10-5bd6df454fd1:wrong-flag'
_expect 2 ai-bs-vm -g playground/aitoolstest -i "$IMAGE" --nova-attach-new-volume 'vdb=1GB:type=foo:delete-on-terminate'

echo "Asking for volumes that don't exit..."
_expect 40 ai-bs-vm -g playground/aitoolstest --nova-boot-from-existing-volume '0207a0b8-9e72-42bd-ae10-5bd6df454fd1'
_expect 40 ai-bs-vm -g playground/aitoolstest  -i "$IMAGE" --nova-attach-existing-volume 'vdb=0207a0b8-9e72-42bd-ae10-5bd6df454fd1'

echo "Checking valid combinations..."
_expect 0 ai-bs-vm -d -g playground/aitoolstest -i "$IMAGE" 
_expect 0 ai-bs-vm -d -g playground/aitoolstest -i "$IMAGE" --nova-boot-from-new-volume '10GB'
_expect 0 ai-bs-vm -d -g playground/aitoolstest -i "$IMAGE" --nova-boot-from-new-volume '10GB:delete-on-terminate'
_expect 0 ai-bs-vm -d -g playground/aitoolstest -i "$IMAGE" --nova-boot-from-new-volume '10GB:type=cp1'
_expect 0 ai-bs-vm -d -g playground/aitoolstest -i "$IMAGE" --nova-boot-from-new-volume '10GB' --nova-attach-new-volume 'vdb=1GB' --nova-attach-new-volume 'vdc=1GB'
_expect 0 ai-bs-vm -d -g playground/aitoolstest -i "$IMAGE" --nova-attach-new-volume 'vdb=1GB:delete-on-terminate' --nova-attach-new-volume 'auto=1GB:type=cp1' --nova-attach-new-volume 'vdd=1GB:delete-on-terminate:type=io1'


echo "Userdata dump..."
_expect 7 ai-bs-vm -d -g playground/aitoolstest -i "$IMAGE" --userdata-dump /etc/passwd
DUMP=$(mktemp -u)
_expect 0 ai-bs-vm -d -g playground/aitoolstest -i "$IMAGE" --userdata-dump $DUMP
_expect 0 stat $DUMP
rm -rf $DUMP

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
