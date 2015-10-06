CONF=$(mktemp)
HIERACONF=$(mktemp)
HIERADATA=$(mktemp -d)
TESTNODE="aifcliftest99.cern.ch"
cat > $CONF << EOF
[foreman]
foreman_hostname = judy.cern.ch
foreman_port = 8443
foreman_timeout = 60

[pdb]
pdb_hostname = judy.cern.ch
pdb_port = 9081
pdb_timeout = 15
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
cat > $HIERACONF << EOF
---
:backends:
   - yaml

:yaml:
   :datadir: $HIERADATA


:hierarchy:
         - environments/%{::foreman_env}/hieradata/fqdns/%{::encgroup_0}/%{::fqdn}
         - environments/%{::foreman_env}/hieradata/hostgroups/%{::encgroup_0}/%{::encgroup_0}/%{::encgroup_1}
         - environments/%{::foreman_env}/hieradata/hostgroups/%{::encgroup_0}/%{::encgroup_0}
         - environments/%{::foreman_env}/hieradata/operatingsystems/%{::osfamily}/%{::operatingsystemmajorrelease}
         - environments/%{::foreman_env}/hieradata/environments/%{::foreman_env}
         - environments/%{::foreman_env}/hieradata/module_names/%{module_name}/%{module_name}
         - environments/%{::foreman_env}/hieradata/hardware/vendor/%{::cern_hwvendor}

:merge_behavior: deeper
EOF

BASEHIERADATA="$HIERADATA/environments/qa/hieradata"
mkdir -p $BASEHIERADATA/environments
mkdir -p $BASEHIERADATA/hostgroups/playground/playground
echo "foo: \"bar\"" >> $BASEHIERADATA/hostgroups/playground/playground.yaml
echo "foo: \"baz\"" >> $BASEHIERADATA/hostgroups/playground/playground/aitoolstest.yaml
echo "foo: \"rocks\"" >> $BASEHIERADATA/environments/qa.yaml
echo "$TESTNODE 192.168.0.1 aa:bb:cc:dd:ee:ff" >> $IN

_expect 0 ai-foreman --config $CONF addhost -c playground/aitoolstest/test1 -e qa \
  -a x86_64 -p "\"Kickstart default\"" -o "\"SLC 6.6\"" -m SLC -r -i $IN

echo "Arguments..."
_expect 2 ai-hiera --config $CONF --hiera-config $HIERACONF -n $TESTNODE

echo "Resolution..."
_expect 0 ai-hiera --config $CONF --hiera-config $HIERACONF -n $TESTNODE foo
_expect 0 ai-hiera --config $CONF --hiera-config $HIERACONF -n $TESTNODE foo -t
_expect 0 ai-hiera --config $CONF --hiera-config $HIERACONF -n $TESTNODE foo -a
_expect 0 ai-hiera --config $CONF --hiera-config $HIERACONF -n $TESTNODE foo --foreman-hostgroup foo
_expect 1 ai-hiera --config $CONF --hiera-config $HIERACONF -n $TESTNODE foo --foreman-environment production
_expect 1 ai-hiera --config $CONF --hiera-config $HIERACONF -n $TESTNODE foo bar
_expect 1 ai-hiera --config $CONF --hiera-config $HIERACONF -n $TESTNODE foo bar -t

echo "Tearing down..."
_expect 0 ai-foreman --config $CONF delhost $TESTNODE
rm -rf $IN $CONF $HIERACONF $HIERADATA
echo "All tests passed :)"