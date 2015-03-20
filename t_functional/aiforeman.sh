# This is a not very nice bash script to do some kind
# of naive functional testing for ai-foreman.

CONF=$(mktemp)
cat > $CONF << EOF
[foreman]
foreman_hostname = judy.cern.ch
foreman_port = 8443
foreman_timeout = 60
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
for i in `seq 16 18`
do
  m=`echo "obase=16; $i" | bc`
  echo "aifcliftest$i.cern.ch 192.168.0.$i aa:bb:cc-dd:ee:$m" >> $IN
done

echo "Arguments"
_expect 2 ai-foreman --config $CONF -z Fail showhost aifcliftest16.cern.ch
_expect 2 ai-foreman --config $CONF -z Name --longtable showhost aifcliftest16.cern.ch

echo "Addhost..."
_expect 0 ai-foreman --config $CONF addhost -c playground/ibarrien/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN
echo "aifcliftest100.cern.ch 192.168.0.100" > $IN
_expect 1 ai-foreman --config $CONF addhost -c playground/ibarrien/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN
echo "aifcliftest101.cern.ch 192.168.0.101 aa:bb:cc:dd:ee:fa fail" > $IN
# If the IPMI interface data is wrong then we ignore it
_expect 0 ai-foreman --config $CONF addhost -c playground/ibarrien/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN

echo "Showhost..."
_expect 0 ai-foreman --config $CONF showhost aifcliftest16.cern.ch
_expect 0 ai-foreman --config $CONF -g playground/ibarrien/test1 showhost aifcliftest16.cern.ch
_expect 0 ai-foreman --config $CONF --longtable -g playground/ibarrien/test1 showhost
_expect 0 ai-foreman --config $CONF -z Name -z Environment -g playground/ibarrien/test1 showhost

echo "Updatehost..."
_expect 0 ai-foreman --config $CONF updatehost -e production aifcliftest16.cern.ch
_expect 1 ai-foreman --config $CONF updatehost --mac foo aifcliftest16.cern.ch
_expect 1 ai-foreman --config $CONF updatehost -o "\"CentOS 7.0\"" \
  aifcliftest17.cern.ch
_expect 0 ai-foreman --config $CONF updatehost -o "\"CentOS 7.0\"" \
  -m "\"CentOS mirror\"" aifcliftest17.cern.ch
_expect 0 ai-foreman --config $CONF -g playground/ibarrien/test1 updatehost \
  -e production -c playground/ibarrien/test2
_expect 0 ai-foreman --config $CONF -g playground/ibarrien/test2 showhost

echo "Delhost..."
_expect 0 ai-foreman --config $CONF delhost  aifcliftest16.cern.ch
_expect 0 ai-foreman --config $CONF -g playground/ibarrien/test2 delhost

echo "Tearing down..."
rm -f $IN $CONF
