
CONF=$(mktemp)
cat > $CONF << EOF
[pwn]
pwn_hostname = teigitest.cern.ch
pwn_port = 8201
pwn_timeout = 15
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

 echo "Arguments"
 _expect 2 ai-pwn --config $CONF show module hostgroup
 _expect 2 ai-pwn --config $CONF show module asd qwe
 _expect 2 ai-pwn --config $CONF set meeee@cern.ch
 _expect 2 ai-pwn --config $CONF set hostgroup myhg --owners meeee --options \"{\'invalid\':\'json\'}\"
 _expect 2 ai-pwn --config $CONF set

 echo "Set ownership..."
 _expect 0 ai-pwn --config $CONF set hostgroup punch/puppetdb/grover --owners ahencz@CERN.CH --options \'{\"valid\": \"json\"}\'
 _expect 0 ai-pwn --config $CONF set module my_module --owners ahencz@CERN.CH ai-config-robots

 echo "Add owners..."
 _expect 0 ai-pwn --config $CONF add hostgroup punch/puppetdb/grover --owners bejones@CERN.CH nacho@CERN.CH
 _expect 0 ai-pwn --config $CONF add module teigi --owners bejones@CERN.CH

 echo "Remove owners..."
 _expect 0 ai-pwn --config $CONF remove hostgroup punch/puppetdb/grover --owners ahencz@CERN.CH
 _expect 3 ai-pwn --config $CONF remove module idontexist --owners bejones@CERN.CH

 echo "Show ownership..."
 _expect 0 ai-pwn --config $CONF show hostgroup punch/puppetdb/grover
 _expect 0 ai-pwn --config $CONF show module teigi
 _expect 0 ai-pwn --config $CONF -v show module my_module
 _expect 3 ai-pwn --config $CONF show module idontexist

 echo "Delete ownership..."
 _expect 0 ai-pwn --config $CONF delete hostgroup punch/puppetdb/grover
 _expect 0 ai-pwn --config $CONF delete module teigi
 _expect 0 ai-pwn --config $CONF delete module my_module


echo "Tearing down..."
rm -f $IN $CONF
echo "All tests passed :)"
