# This is a not very nice bash script to do some kind
# of naive functional testing for ai-installhost.

CONF=$(mktemp)
cat > $CONF << EOF
[foreman]
foreman_hostname = judy.cern.ch
foreman_port = 8443
foreman_timeout = 60

[roger]
roger_hostname = woger.cern.ch
roger_port = 8201
roger_timeout = 15

[certmgr]
certmgr_hostname = baby02.cern.ch
certmgr_port = 8008
certmgr_timeout = 15
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

echo "Arguments"
_expect 2 ai-installhost --config $CONF

# Basically to test parameters :/
echo "Installhost..."
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch --console ttyS0
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch
_expect 1 ai-installhost --config $CONF -d wonteverexist444.cern.ch -k -a

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
