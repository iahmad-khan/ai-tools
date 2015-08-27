# This is a not very nice bash script to do some kind
# of naive functional testing for ai-rc

CONF=$(mktemp)
cat > $CONF << EOF

[DEFAULT]
dereference_alias = true

[pdb]
pdb_hostname = judy.cern.ch
pdb_port = 9081
pdb_timeout = 15
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

echo "Wrong combinations of arguments"
_expect 2 ai-rc --same-project-as lxplusfake001 "LXBATCH"

echo "Machine not in DNS"
_expect 1 ai-rc --same-project-as lxplusfake001

echo "Happy path"
_expect 0 ai-rc
_expect 0 ai-rc --same-project-as lxplus
_expect 0 ai-rc -s lxplus
_expect 0 ai-rc "LXPLUS"
_expect 0 ai-rc -s lxplus -c
_expect 0 ai-rc "LXPLUS" -c

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
