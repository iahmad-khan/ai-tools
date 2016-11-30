#!/bin/bash
# This is a not very nice bash script to do some kind
# of naive functional testing for ai-foreman.

source "$(dirname "$0")/common.sh"

CONF=$(mktemp)
cat > $CONF << EOF
[foreman]
foreman_hostname = ${FOREMAN_HOSTNAME}
foreman_port = 8443
foreman_timeout = 60
EOF
IN=$(mktemp)

echo "Setting up..."
for i in `seq 16 18`
do
  m=`echo "obase=16; $i" | bc`
  echo "aifcliftest$i.cern.ch 192.168.0.$i aa:bb:cc-dd:ee:$m" >> $IN
done

echo "Arguments"
_expect 2 ai-foreman --config $CONF -g foo -l foo showhost
_expect 2 ai-foreman --config $CONF --only-error -f "foo" howhost
_expect 2 ai-foreman --config $CONF --only-error --only-oos foo showhost
_expect 2 ai-foreman --config $CONF addhost showhost aifcliftest16.cern.ch
_expect 2 ai-foreman --config $CONF -z Fail showhost aifcliftest16.cern.ch
_expect 2 ai-foreman --config $CONF -s Fail showhost aifcliftest16.cern.ch
_expect 2 ai-foreman --config $CONF -z Name --longtable showhost aifcliftest16.cern.ch

echo "Krb"
_expect 4 KRB5CCNAME="FILE:blahblah" ai-foreman --config $CONF showhost foo.cern.ch

echo "Addhost..."
_expect 0 ai-foreman --config $CONF addhost -c playground/aitoolstest/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN
echo "aifcliftest100.cern.ch 192.168.0.100" > $IN
_expect 1 ai-foreman --config $CONF addhost -c playground/aitoolstest/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN
echo "aifcliftest101.cern.ch 192.168.0.101 aa:bb:cc:dd:ee:fa fail" > $IN
# If the IPMI interface data is wrong then we ignore it
_expect 0 ai-foreman --config $CONF addhost -c playground/aitoolstest/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN

echo "Showhost..."
_expect 0 ai-foreman --config $CONF showhost aifcliftest16.cern.ch
_expect 0 ai-foreman --config $CONF --no-header showhost aifcliftest16.cern.ch
_expect 0 ai-foreman --config $CONF -g playground/aitoolstest/test1 showhost aifcliftest16.cern.ch
_expect 0 ai-foreman --config $CONF --longtable -g playground/aitoolstest/test1 showhost
_expect 1 ai-foreman --config $CONF -g willneverexist5555 showhost
_expect 0 ai-foreman --config $CONF -z Name -z Environment -g playground/aitoolstest/test1 showhost
_expect 0 ai-foreman --config $CONF -z Name -z Environment -s Environment -g playground/aitoolstest/test1 showhost

echo "Updatehost..."
_expect 0 ai-foreman --config $CONF updatehost -e production aifcliftest16.cern.ch

# Test if environment is preserved after update the host (targets issues with Foreman v2 API)
_expect 1 ai-foreman --config $CONF updatehost aifcliftest16.cern.ch \
  -c playground/aitoolstest --after | grep -i None
_expect 1 ai-foreman --config $CONF updatehost aifcliftest16.cern.ch \
  -e qa --after | grep -i None

_expect 1 ai-foreman --config $CONF updatehost --mac foo aifcliftest16.cern.ch
_expect 1 ai-foreman --config $CONF updatehost -o "\"CentOS 7.0\"" \
  aifcliftest17.cern.ch
_expect 0 ai-foreman --config $CONF updatehost -o "\"RHEL Server 7.2\"" \
  -m "\"RedHat\"" aifcliftest17.cern.ch
_expect 0 ai-foreman --config $CONF updatehost -o "\"SLC 6.7\"" \
  -m "\"SLC\"" aifcliftest17.cern.ch
_expect 0 ai-foreman --config $CONF updatehost -o "\"CentOS 7.0\"" \
  -m "\"CentOS mirror\"" aifcliftest17.cern.ch
_expect 0 ai-foreman --config $CONF -g playground/aitoolstest/test1 updatehost \
  -e production -c playground/aitoolstest/test2
_expect 0 ai-foreman --config $CONF -g playground/aitoolstest/test2 showhost

echo "Delhost..."
_expect 0 ai-foreman --config $CONF delhost aifcliftest16.cern.ch
_expect 0 ai-foreman --config $CONF -g playground/aitoolstest/test2 delhost

echo "Createhostgroup..."
_expect 1 ai-foreman --config $CONF addhostgroup nonexistingyet/tsetslootia1
_expect 0 ai-foreman --config $CONF addhostgroup playground/tsetslootia1
_expect 0 ai-foreman --config $CONF addhostgroup playground/aitoolstest/new1
_expect 1 ai-foreman --config $CONF addhostgroup playground/nonexistingyet/new
_expect 1 ai-foreman --config $CONF addhostgroup playground/aitoolstest/testA1/testB1/testC1/testD1/testE1
_expect 1 ai-foreman --config $CONF addhostgroup playground/aitoolstest/nonexistingyet/new playground/aitoolstest/another1

_expect 0 ai-foreman --config $CONF addhostgroup -p playground/tsetslootia2
_expect 0 ai-foreman --config $CONF addhostgroup -p playground/aitoolstest/new2
_expect 0 ai-foreman --config $CONF addhostgroup -p playground/nonexistingyet/new
_expect 0 ai-foreman --config $CONF addhostgroup -p playground/aitoolstest/testA2/testB2/testC2/testD2/testE2
_expect 0 ai-foreman --config $CONF addhostgroup -p playground/aitoolstest/nonexistingyet/new playground/aitoolstest/another2


echo "Delhostgroup..."
_expect 0 ai-foreman --config $CONF delhostgroup playground/tsetslootia1
_expect 0 ai-foreman --config $CONF delhostgroup playground/tsetslootia2
_expect 0 ai-foreman --config $CONF delhostgroup playground/aitoolstest/new1
_expect 0 ai-foreman --config $CONF delhostgroup playground/aitoolstest/new2
_expect 1 ai-foreman --config $CONF delhostgroup playground/nonexistingyet
_expect 0 ai-foreman --config $CONF delhostgroup playground/nonexistingyet -R
_expect 0 ai-foreman --config $CONF delhostgroup playground/aitoolstest/nonexistingyet playground/aitoolstest/another1 playground/aitoolstest/another2 -R

_expect 1 ai-foreman --config $CONF delhostgroup playground/aitoolstest/testA2/testB2/testC2/testD2
_expect 1 ai-foreman --config $CONF delhostgroup playground/aitoolstest/testA2/testB2/testC2
_expect 1 ai-foreman --config $CONF delhostgroup playground/aitoolstest/testA2/testB2
_expect 1 ai-foreman --config $CONF delhostgroup playground/aitoolstest/testA2
_expect 1 ai-foreman --config $CONF delhostgroup playground/aitoolstest

_expect 0 ai-foreman --config $CONF delhostgroup playground/aitoolstest/testA2 -R

# deleting hostgroup with host
_expect 0 ai-foreman --config $CONF addhostgroup playground/hgwithhost
IN2=$(mktemp)
echo "aifcliftest42.cern.ch 192.168.0.42 aa:bb:cc-dd:ee:42" >> $IN2
_expect 0 ai-foreman --config $CONF addhost -c playground/hgwithhost -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -i $IN2
_expect 1 ai-foreman --config $CONF delhostgroup playground/hgwithhost
_expect 0 ai-foreman --config $CONF delhost aifcliftest42.cern.ch
_expect 0 ai-foreman --config $CONF delhostgroup playground/hgwithhost


echo "Tearing down..."
rm -f $IN $IN2 $CONF
echo "All tests passed :)"
