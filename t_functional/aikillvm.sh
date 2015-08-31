CONF=$(mktemp)
TESTNODE="aifcliftest99.cern.ch"
cat > $CONF << EOF
[foreman]
foreman_hostname = judy.cern.ch
foreman_port = 8443
foreman_timeout = 60

[roger]
roger_hostname = woger.cern.ch
roger_port = 8201
roger_timeout = 15

[nova]
nova_timeout = 45
EOF
IN=$(mktemp)

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

echo "Setting up..."
echo "$TESTNODE 192.168.0.1 aa:bb:cc:dd:ee:ff" >> $IN
_expect 0 ai-foreman --config $CONF addhost -c playground/aitoolstest/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN

echo "Arguments..."
_expect 2 ai-kill-vm --config $CONF
_expect 2 ai-kill-vm --config $CONF foo bar

#Cannot be tested here as it requires the OS entry to exist
#echo "Dryrun..."
#_expect 0 ai-kill-vm --config $CONF -d $TESTNODE

echo "Foreman..."
_expect 0 ai-kill-vm --config $CONF --nova-disable --roger-disable $TESTNODE

echo "Tearing down..."
# Must fail as the call above should have deleted the node
_expect 1 ai-foreman --config $CONF delhost $TESTNODE
rm -rf $IN $CONF
echo "All tests passed :)"
