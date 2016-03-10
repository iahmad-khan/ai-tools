import unittest
from mock import Mock, patch
from requests.exceptions import Timeout
from aitools.errors import AiToolsGlanceError
from aitools.glance import GlanceClient as GlanceWrapper
from aitools.openstack_auth_client import OpenstackAuthClient
from glanceclient.exc import ClientException

class TestGlance(unittest.TestCase):

    def setUp(self):
        OpenstackAuthClient = Mock(session='')
        self.tenant = GlanceWrapper(auth_client=OpenstackAuthClient(), timeout=10)

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_timeout(self, mock_tenant):
        mock_tenant.return_value.images.list.side_effect = Timeout
        self.assertRaises(AiToolsGlanceError, self.tenant.get_latest_image, 'CC', '7')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_client_exception(self, mock_tenant):
        mock_tenant.return_value.images.list.side_effect = ClientException('Error!')
        self.assertRaises(AiToolsGlanceError, self.tenant.get_latest_image, 'CC', '7')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_uncaught(self, mock_tenant):
        mock_tenant.return_value.images.list.side_effect = Exception
        try:
            self.tenant.get_latest_image('CC', '7')
        except AiToolsGlanceError:
            self.fail("It shouldn't be an AiToolsGlanceError")
        except Exception:
            mock_tenant.assert_called_once()
        else:
            self.fail("It should throw an exception")

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_not_found(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'SLC',
            'os_distro_major': '6',
            'os_distro_minor': '2',
            'os_edition': 'Server',
            'architecture': 'x86_64',
            'release_date': '2013-06-24'
        }]
        self.assertRaises(AiToolsGlanceError, self.tenant.get_latest_image, 'CC', '7')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_wrong_arch(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'SLC',
            'os_distro_major': 6,
            'os_distro_minor': 2,
            'os_edition': 'Server',
            'architecture': 'x86_64',
            'release_date': '2013-06-24'
        }]
        self.assertRaises(AiToolsGlanceError, self.tenant.get_latest_image, 'SLC', '6', 'Server', 'i686')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_found1(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'SLC',
            'os_distro_major': '6',
            'os_distro_minor': '2',
            'os_edition': 'Server',
            'architecture': 'x86_64',
            'release_date': '2013-06-24'
        }]
        self.assertTrue(self.tenant.get_latest_image('SLC', '6', 'Server'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_found2(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'SLC',
            'os_distro_major': '6',
            'os_distro_minor': '2',
            'os_edition': 'Server',
            'architecture': 'x86_64',
            'release_date': '2015-06-24'
        },
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'SLC',
            'os_distro_major': '6',
            'os_edition': 'Server',
            'architecture': 'x86_64',
            'release_date': '2015-06-25',
            'os_distro_minor': '2'
        }]
        self.assertTrue(self.tenant.get_latest_image('SLC', '6', 'Server'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_found_reverse(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-06-25',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-06-24',
            'os_distro_minor': '2'
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_found_minor_first_same_date(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-06-25',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-06-25',
            'os_distro_minor': '1',
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_image_found_minor_first_older(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2016-06-25',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-06-25',
            'os_distro_minor': '3',
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_different_os_distro(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'SLC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2016-06-25',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2016-06-25',
            'os_distro_minor': '2'
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_different_os_distro_major(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2016-06-25',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '6',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2016-06-25',
            'os_distro_minor': '2'
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_hours(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-09-03T15:31:59',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-09-03T09:43:41',
            'os_distro_minor': '2'
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_latest_hours2(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-09-03T08:31:59',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-09-03T09:43:41',
            'os_distro_minor': '2'
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')


    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_image_no_metadata_is_ignored(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2016-06-25',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            'abcd-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_only_publics_private_newer(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': 'abcd-68e1-4969-b26a-64022e87ef28',
            'visibility': 'private',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-09-03T10:31:59',
            'os_distro_minor': '2'
        },
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'public',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-09-03T09:43:41',
            'os_distro_minor': '2'
        }]
        self.assertTrue(self.tenant.get_latest_image('CC', '7'),
            '49e166bb-68e1-4969-b26a-64022e87ef28')

    @patch.object(GlanceWrapper, '_GlanceClient__init_client')
    def test_get_only_publics_no_publics(self, mock_tenant):
        mock_tenant.return_value.images.list.return_value = [
        {
            'id': '49e166bb-68e1-4969-b26a-64022e87ef28',
            'visibility': 'private',
            'os_distro': 'CC',
            'os_distro_major': '7',
            'os_edition': 'Base',
            'architecture': 'x86_64',
            'release_date': '2015-09-03T09:43:41',
            'os_distro_minor': '2'
        }]
        self.assertRaises(AiToolsGlanceError, self.tenant.get_latest_image, 'CC', '7')
