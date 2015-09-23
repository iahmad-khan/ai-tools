__author__ = 'Alberto Rodriguez Peon'

import unittest
from mock import Mock, patch
from requests.exceptions import Timeout
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


    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_timeout(self, mock_tenant):
        mock_tenant.return_value.images.list.side_effect = Timeout
        self.assertRaises(AiToolsNovaError, self.tenant.get_latest_image, 'CC', '7')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_client_exception(self, mock_tenant):
        mock_tenant.return_value.images.list.side_effect = ClientException('Error!')
        self.assertRaises(AiToolsNovaError, self.tenant.get_latest_image, 'CC', '7')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_connection_refused(self, mock_tenant):
        mock_tenant.return_value.images.list.side_effect = ConnectionRefused
        self.assertRaises(AiToolsNovaError, self.tenant.get_latest_image, 'CC', '7')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_uncaught(self, mock_tenant):
        mock_tenant.return_value.images.list.side_effect = Exception
        try:
            self.tenant.get_latest_image('CC', '7')
        except AiToolsNovaError:
            self.fail("It shouldn't be an AiToolsNovaError")
        except Exception:
            mock_tenant.assert_called_once()
        else:
            self.fail("It should throw an exception")

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_not_found(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'SLC',
                'os_distro_major': '6',
                'os_distro_minor': '2',
                'os_edition': 'Server',
                'architecture': 'x86_64',
                'release_date': '2013-06-24'
            }
        })]
        self.assertRaises(AiToolsNovaError, self.tenant.get_latest_image, 'CC', '7')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_wrong_arch(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'SLC',
                'os_distro_major': 6,
                'os_distro_minor': 2,
                'os_edition': 'Server',
                'architecture': 'x86_64',
                'release_date': '2013-06-24'
            }
        })]
        self.assertRaises(AiToolsNovaError, self.tenant.get_latest_image, 'SLC', '6', 'Server', 'i686')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_found1(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'SLC',
                'os_distro_major': '6',
                'os_distro_minor': '2',
                'os_edition': 'Server',
                'architecture': 'x86_64',
                'release_date': '2013-06-24'
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('SLC', '6', 'Server'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_found2(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'SLC',
                'os_distro_major': '6',
                'os_distro_minor': '2',
                'os_edition': 'Server',
                'architecture': 'x86_64',
                'release_date': '2015-06-24'
            }
        }),
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'SLC',
                'os_distro_major': '6',
                'os_edition': 'Server',
                'architecture': 'x86_64',
                'release_date': '2015-06-25',
                'os_distro_minor': '2'
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('SLC', '6', 'Server'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_found_reverse(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-06-25',
                'os_distro_minor': '2'
            }
        }),
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-06-24',
                'os_distro_minor': '2'
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_found_minor_first_same_date(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-06-25',
                'os_distro_minor': '2'
            }
        }),
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-06-25',
                'os_distro_minor': '1',
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_image_found_minor_first_older(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2016-06-25',
                'os_distro_minor': '2'
            }
        }),
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-06-25',
                'os_distro_minor': '3',
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_different_os_distro(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'SLC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2016-06-25',
                'os_distro_minor': '2'
            }
        }),
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2016-06-25',
                'os_distro_minor': '2'
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_different_os_distro_major(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2016-06-25',
                'os_distro_minor': '2'
            }
        }),
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '6',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2016-06-25',
                'os_distro_minor': '2'
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_hours(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-09-03T15:31:59',
                'os_distro_minor': '2'
            }
        }),
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-09-03T09:43:41',
                'os_distro_minor': '2'
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_latest_hours2(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-09-03T08:31:59',
                'os_distro_minor': '2'
            }
        }),
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2015-09-03T09:43:41',
                'os_distro_minor': '2'
            }
        })]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')


    @patch.object(NovaWrapper, '_NovaClient__init_client')
    def test_get_image_no_metadata_is_ignored(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        Mock(to_dict=lambda:{
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'metadata': {
                'os_distro': 'CC',
                'os_distro_major': '7',
                'os_edition': 'Base',
                'architecture': 'x86_64',
                'release_date': '2016-06-25',
                'os_distro_minor': '2'
            }
        }),
        Mock(to_dict=lambda:{
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
        })]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')
