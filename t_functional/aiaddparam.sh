# This is a not very nice bash script to do some kind
# of naive functional testing for ai-add-param

CONF=$(mktemp)
cat > $CONF << EOF
[foreman]
foreman_hostname = judy.cern.ch
foreman_port = 8443
foreman_timeout = 60
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


_expect 0 ai-add-param --hg playground/aitoolstest foo bar
_expect 0 ai-add-param --hg playground/aitoolstest foo bar
_expect 0 ai-add-param --hg playground/aitoolstest foo bar2
_expect 0 ai-add-param nachodev03.cern.ch foo2 bar2
_expect 0 ai-add-param nachodev03.cern.ch foo2 bar2
_expect 0 ai-add-param nachodev03.cern.ch foo2 bar3

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"