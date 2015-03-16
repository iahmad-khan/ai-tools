# This is a stupid bash script to do some kind
# of functional testing for ai-foreman.
set -ex

CONF=$(mktemp)
cat > $CONF << EOF
[foreman]
foreman_hostname = judy.cern.ch
foreman_port = 8443
foreman_timeout = 60
EOF
IN=$(mktemp)

echo "aifcliftest10.cern.ch 192.168.0.2 aa:bb:cc:dd:ee:FF" > $IN
echo "aifcliftest11.cern.ch 192.168.0.3 aa-bb-cc-dd-ee-FE" >> $IN
echo "aifcliftest12.cern.ch 192.168.0.4 AA:bb:cc:dd:ee:FD" >> $IN
cat $IN | ai-foreman --config $CONF addhost -c playground/ibarrien/test1 -e qa -a x86_64 -p "Kickstart default" -o "SLC 6.6" -m "SLC" -r
echo "Showhost..."
ai-foreman --config $CONF showhost aifcliftest10.cern.ch
ai-foreman --config $CONF -g playground/ibarrien/test1 showhost aifcliftest10.cern.ch
ai-foreman --config $CONF -g playground/ibarrien/test1 showhost
echo "Updatehost..."
ai-foreman --config $CONF updatehost -e production aifcliftest10.cern.ch -y
ai-foreman --config $CONF updatehost -o "CentOS 7.0" -m "CentOS mirror" aifcliftest11.cern.ch -y
ai-foreman --config $CONF -g playground/ibarrien/test1 updatehost -e production -c playground/ibarrien/test2 -y
ai-foreman --config $CONF -g playground/ibarrien/test2 showhost
echo "Delhost..."
ai-foreman --config $CONF delhost -y aifcliftest10.cern.ch
ai-foreman --config $CONF -g playground/ibarrien/test2 delhost -y
rm $IN $CONF
