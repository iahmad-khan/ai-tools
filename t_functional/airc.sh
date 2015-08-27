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
_expect 0 "ai-rc --same-project-as lxplus -c | grep -q unsetenv"
_expect 0 "ai-rc -s lxplus -c | grep -q unsetenv"
_expect 0 "ai-rc 'LXPLUS' --cshell | grep -q unsetenv"
_expect 0 "ai-rc --same-project-as lxplus -b | grep -q export"
_expect 0 "ai-rc -s lxplus --bshell | grep -q export"
_expect 0 "ai-rc 'LXPLUS' -b | grep -q export"
_expect 0 "SHELL='/bin/tcsh' ai-rc 'LXBATCH' | grep -q unsetenv"
_expect 0 "SHELL='/bin/bash' ai-rc 'LXBATCH' | grep -q export"
_expect 0 "SHELL='' ai-rc 'LXBATCH' | grep -q export"
_expect 0 "SHELL='diegocervero' ai-rc 'LXBATCH' | grep -q export"

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
