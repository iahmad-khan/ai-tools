
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
 _expect 2 ai-ownership --config $CONF set --hg myhg --md mymod meeee@cern.ch
 _expect 2 ai-ownership --config $CONF set meeee@cern.ch
 _expect 2 ai-ownership --config $CONF set --hg myhg meeee --options \"{\'invalid\':\'json\'}\"
 _expect 2 ai-ownership --config $CONF set

 echo "Set ownership..."
 _expect 0 ai-ownership --config $CONF set --hg punch/puppetdb/grover ahencz@CERN.CH --options \'{\"valid\": \"json\"}\'
 _expect 0 ai-ownership --config $CONF set --md my_module ahencz@CERN.CH ai-config-robots

 echo "Add owners..."
 _expect 0 ai-ownership --config $CONF add --hg punch/puppetdb/grover bejones@CERN.CH nacho@CERN.CH
 _expect 0 ai-ownership --config $CONF add --md teigi bejones@CERN.CH

 echo "Remove owners..."
 _expect 0 ai-ownership --config $CONF remove --hg punch/puppetdb/grover ahencz@CERN.CH
 _expect 2 ai-ownership --config $CONF remove --md idontexist bejones@CERN.CH

 echo "Show ownership..."
 _expect 0 ai-ownership --config $CONF show --hg punch/puppetdb/grover
 _expect 0 ai-ownership --config $CONF show --md teigi
 _expect 0 ai-ownership --config $CONF -v show --md my_module
 _expect 2 ai-ownership --config $CONF show --md idontexist

 echo "Delete ownership..."
 _expect 0 ai-ownership --config $CONF delete --hg punch/puppetdb/grover
 _expect 0 ai-ownership --config $CONF delete --md teigi
 _expect 0 ai-ownership --config $CONF delete --md my_module


echo "Tearing down..."
rm -f $IN $CONF
echo "All tests passed :)"
