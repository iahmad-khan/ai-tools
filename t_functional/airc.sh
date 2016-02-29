#!/bin/bash
# This is a not very nice bash script to do some kind
# of naive functional testing for ai-rc

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
cat > $CONF << EOF

[DEFAULT]
dereference_alias = true

[pdb]
pdb_hostname = judy.cern.ch
pdb_port = 9081
pdb_timeout = 15
EOF

echo "Wrong combinations of arguments"
_expect 2 ai-rc --config $CONF --same-project-as lxplusfake001 "LXBATCH"

echo "Machine not in DNS"
_expect 1 ai-rc --config $CONF --same-project-as lxplusfake001

echo "Happy path"
_expect 0 ai-rc --config $CONF
_expect 0 ai-rc --config $CONF --same-project-as lxplus
_expect 0 ai-rc --config $CONF -s lxplus
_expect 0 ai-rc --config $CONF "LXPLUS"
_expect 0 "ai-rc --config $CONF --same-project-as lxplus -c | grep -q unsetenv"
_expect 0 "ai-rc --config $CONF -s lxplus -c | grep -q unsetenv"
_expect 0 "ai-rc --config $CONF 'LXPLUS' --cshell | grep -q unsetenv"
_expect 0 "ai-rc --config $CONF --same-project-as lxplus -b | grep -q export"
_expect 0 "ai-rc --config $CONF -s lxplus --bshell | grep -q export"
_expect 0 "ai-rc --config $CONF 'LXPLUS' -b | grep -q export"
_expect 0 "SHELL='/bin/tcsh' ai-rc --config $CONF 'LXBATCH' | grep -q unsetenv"
_expect 0 "SHELL='/bin/bash' ai-rc --config $CONF 'LXBATCH' | grep -q export"
_expect 0 "SHELL='' ai-rc --config $CONF 'LXBATCH' | grep -q export"
_expect 0 "SHELL='diegocervero' ai-rc --config $CONF 'LXBATCH' | grep -q export"

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
