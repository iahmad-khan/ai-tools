CONF=$(mktemp)
cat > $CONF << EOF
[foreman]
foreman_hostname = judy.cern.ch
foreman_port = 8443
foreman_timeout = 60
EOF

FECACHE=$(mktemp)
cat > $FECACHE << EOF
{"Configuration Management": "Imfake"}
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

_expect 0 ai-set-fe --fecache $FECACHE --hostgroup playground/aitoolstest \"Configuration Management\"
_expect 3 ai-set-fe --fecache $FECACHE --hostgroup playground/aitoolstest \"This will never exist\"
_expect 0 ai-set-fe --fecache $FECACHE --hostgroup playground/aitoolstest Ignore
_expect 4 ai-set-fe --fecache $FECACHE --hostgroup hope/this/will/never/exist Ignore

echo "Tearing down..."
rm -f $CONF
echo "All tests passed :)"
