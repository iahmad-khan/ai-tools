__author__ = 'Alberto Rodriguez Peon'

import unittest
from mock import Mock, patch
from aitools.errors import AiToolsNovaError
from aitools.nova import NovaClient as NovaWrapper
from aitools.openstack_auth_client import OpenstackAuthClient
from novaclient.v1_1 import client as novaAPI
from novaclient.v1_1 import servers
from novaclient.exceptions import ClientException, ConnectionRefused
from uuid import uuid4

class TestNova(unittest.TestCase):

    def setUp(self):
        OpenstackAuthClient = Mock(session='')
        self.tenant = NovaWrapper(auth_client=OpenstackAuthClient(), timeout=10)
        self.fake_uuid = lambda: str(uuid4())

    def set_up_for_rebuild(test):
        @patch.object(NovaWrapper, '_NovaClient__init_client')
        @patch.object(NovaWrapper, '_NovaClient__vmname_from_fqdn', return_value='fake.cern.ch')
        @patch.object(NovaWrapper, '_NovaClient__resolve_id', return_value='cf5003bc-4dc1-4212-bb4a-2c75aa70ded6')
        def run_test_for_rebuild(*args, **kwargs):
            test(*args, **kwargs)
        return run_test_for_rebuild


    @patch.object(novaAPI.Client, '__init__', side_effect=ClientException('Client exception!'))
    def test_client_error_in_cinder_init_client(self, mock_client):
        self.assertRaises(AiToolsNovaError, self.tenant._NovaClient__init_client)
        mock_client.assert_called_once()

    @patch.object(novaAPI.Client, '__init__', side_effect=ConnectionRefused)
    def test_connection_error_in_cinder_init_client(self, mock_client):
        self.assertRaises(AiToolsNovaError, self.tenant._NovaClient__init_client)
        mock_client.assert_called_once()

    @patch.object(novaAPI.Client, '__init__', side_effect=Exception)
    def test_uncaught_exception_in_cinder_init_client(self, mock_client):
        try:
            self.tenant._NovaClient__init_client()
        except AiToolsNovaError:
            self.fail("It shouldn't be an AiToolsNovaError")
        except Exception:
            mock_client.assert_called_once()
        else:
            self.fail("It should throw an exception")

    @set_up_for_rebuild
    def test_rebuild_same_image(self, mock_resolve_id, mock_vmname, mock_tenant):
        server = Mock(spec=servers.Server, image={'id' : self.fake_uuid()})
        mock_tenant.return_value.servers.get.return_value = server

        self.tenant.rebuild('fake.cern.ch', image=None)

        self.tenant._NovaClient__vmname_from_fqdn.assert_called_once_with('fake.cern.ch')
        self.tenant._NovaClient__init_client.assert_called_once()
        self.tenant._NovaClient__resolve_id.assert_called_once()
        mock_tenant.return_value.servers.get.assert_called_once_with(mock_resolve_id())
        server.rebuild.assert_called_once_with(image=server.image['id'])

    @set_up_for_rebuild
    def test_rebuild_different_image(self, mock_resolve_id, mock_vmname, mock_tenant):
        server = Mock(spec=servers.Server, image={'id' : self.fake_uuid()})
        mock_tenant.return_value.servers.get.return_value = server

        new_image = self.fake_uuid()
        self.tenant.rebuild('fake.cern.ch', image=new_image)

        self.tenant._NovaClient__vmname_from_fqdn.assert_called_once_with('fake.cern.ch')
        self.tenant._NovaClient__init_client.assert_called_once()
        self.tenant._NovaClient__resolve_id.assert_called_once()
        mock_tenant.return_value.servers.get.assert_called_once_with(mock_resolve_id())
        server.rebuild.assert_called_once_with(image=new_image)

    @set_up_for_rebuild
    def test_rebuild_from_volume_same_image(self, mock_resolve_id, mock_vmname, mock_tenant):
        server = Mock(spec=servers.Server, image='')
        mock_tenant.return_value.servers.get.return_value = server

        self.assertRaises(AiToolsNovaError, self.tenant.rebuild, 'fake.cern.ch', image=None)
        self.tenant._NovaClient__vmname_from_fqdn.assert_called_once_with('fake.cern.ch')
        self.tenant._NovaClient__init_client.assert_called_once()
        self.tenant._NovaClient__resolve_id.assert_called_once()

    @set_up_for_rebuild
    def test_rebuild_from_volume_different_image(self, mock_resolve_id, mock_vmname, mock_tenant):
        server = Mock(spec=servers.Server, image='')
        mock_tenant.return_value.servers.get.return_value = server

        new_image = self.fake_uuid()
        self.assertRaises(AiToolsNovaError, self.tenant.rebuild, 'fake.cern.ch', image=new_image)
        self.tenant._NovaClient__vmname_from_fqdn.assert_called_once_with('fake.cern.ch')
        self.tenant._NovaClient__init_client.assert_called_once()
        self.tenant._NovaClient__resolve_id.assert_called_once()
