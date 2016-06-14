__author__ = 'Alberto Rodriguez Peon'

import unittest
from mock import Mock, patch
from requests.exceptions import Timeout
from aitools.cinder import CinderClient as CinderWrapper
from aitools.errors import AiToolsCinderError
from cinderclient.exceptions import ClientException, ConnectionError, NotFound
from cinderclient.v2 import client as cinderAPI
from cinderclient.v2 import volumes
from aitools.openstack_auth_client import OpenstackAuthClient


class TestCinder(unittest.TestCase):

    def setUp(self):
        OpenstackAuthClient = Mock(session='')
        self.tenant = CinderWrapper(auth_client=OpenstackAuthClient())

    @patch.object(cinderAPI.Client, '__init__', side_effect=ClientException('Client exception!'))
    def test_client_error_in_cinder_init_client(self, mock_client):
        self.assertRaises(AiToolsCinderError, self.tenant._CinderClient__init_client)
        mock_client.assert_called_once()

    @patch.object(cinderAPI.Client, '__init__', side_effect=ConnectionError)
    def test_connection_error_in_cinder_init_client(self, mock_client):
        self.assertRaises(AiToolsCinderError, self.tenant._CinderClient__init_client)
        mock_client.assert_called_once()

    @patch.object(cinderAPI.Client, '__init__', side_effect=Timeout)
    def test_timeout_error_in_cinder_init_client(self, mock_client):
        self.assertRaises(AiToolsCinderError, self.tenant._CinderClient__init_client)
        mock_client.assert_called_once()

    @patch.object(cinderAPI.Client, '__init__', side_effect=Exception)
    def test_uncaught_exception_in_cinder_init_client(self, mock_client):
        try:
            self.tenant._CinderClient__init_client()
        except AiToolsCinderError:
            self.fail("It shouldn't be an AiToolsCinderError")
        except Exception:
            mock_client.assert_called_once()
        else:
            self.fail("It should throw an exception")

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_volume_not_found_in_cinder_get(self, mock_tenant):
        mock_tenant.return_value.volumes.get = Mock(side_effect=NotFound(''))
        self.assertRaises(AiToolsCinderError, self.tenant.get, volume_id=1)
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.get.assert_called_once_with(volume_id=1)

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_timeout_in_cinder_get(self, mock_tenant):
        mock_tenant.return_value.volumes.get = Mock(side_effect=Timeout)
        self.assertRaises(AiToolsCinderError, self.tenant.get, volume_id=1)
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.get.assert_called_once_with(volume_id=1)

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_client_error_in_cinder_get(self, mock_tenant):
        mock_tenant.return_value.volumes.get = Mock(side_effect=ClientException(''))
        self.assertRaises(AiToolsCinderError, self.tenant.get, volume_id=1)
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.get.assert_called_once_with(volume_id=1)

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_connection_error_in_cinder_get(self, mock_tenant):
        mock_tenant.return_value.volumes.get = Mock(side_effect=ConnectionError)
        self.assertRaises(AiToolsCinderError, self.tenant.get, volume_id=1)
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.get.assert_called_once_with(volume_id=1)

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_happy_path_in_cinder_get(self, mock_tenant):
        mock_tenant.return_value.volumes.get.return_value = Mock(spec=volumes.Volume,
            id=1, status='available', bootable='true')
        volume = self.tenant.get(volume_id=1)
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.get.assert_called_once_with(volume_id=1)
        self.assertTrue(isinstance(volume, volumes.Volume))

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_uncaught_exception_in_cinder_get(self, mock_tenant):
        mock_tenant.return_value.volumes.get = Mock(side_effect=Exception)
        try:
            self.tenant.get(volume_id=1)
        except AiToolsCinderError:
            self.fail("It shouldn't be an AiToolsCinderError")
        except Exception:
            mock_tenant.assert_called_once_with()
            mock_tenant.return_value.volumes.get.assert_called_once_with(volume_id=1)
        else:
            self.fail("It should throw an exception")

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_dry_run_in_cinder_create(self, mock_tenant):
        self.tenant.dryrun = True
        mock_tenant.return_value.volumes.create = Mock()
        self.assertTrue(self.tenant.create(size='1GB') is None)
        mock_tenant.assert_called_once_with()
        self.assertFalse(mock_tenant.return_value.volumes.create.called)

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_timeout_in_cinder_create(self, mock_tenant):
        mock_tenant.return_value.volumes.create = Mock(side_effect=Timeout('error'))
        self.assertRaises(AiToolsCinderError, self.tenant.create, size=1)
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.create.assert_called_once_with(size=1, volume_type=None,
            name=None, imageRef=None, description=None)

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_client_exception_in_cinder_create(self, mock_tenant):
        mock_tenant.return_value.volumes.create = Mock(side_effect=ClientException('error'))
        self.assertRaises(AiToolsCinderError, self.tenant.create, size=1)
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.create.assert_called_once_with(size=1, volume_type=None,
            name=None, imageRef=None, description=None)

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_connection_error_in_cinder_create(self, mock_tenant):
        mock_tenant.return_value.volumes.create = Mock(side_effect=ConnectionError('error'))
        self.assertRaises(AiToolsCinderError, self.tenant.create, size='1TB')
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.create.assert_called_once_with(size=1024, volume_type=None,
            name=None, imageRef=None, description=None)

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_uncaught_exception_in_cinder_create(self, mock_tenant):
        mock_tenant.return_value.volumes.create = Mock(side_effect=Exception('error'))
        try:
            self.tenant.create(size=1)
        except AiToolsCinderError:
            self.fail("It shouldn't be an AiToolsCinderError")
        except Exception:
            mock_tenant.assert_called_once_with()
            mock_tenant.return_value.volumes.create.assert_called_once_with(size=1, volume_type=None,
            name=None, imageRef=None, description=None)
        else:
            self.fail("It should throw an exception")

    @patch.object(CinderWrapper, '_CinderClient__init_client')
    def test_volume_created_in_cinder_create(self, mock_tenant):
        mock_tenant.return_value.volumes.create.return_value = Mock(spec=volumes.Volume)
        volume = self.tenant.create(size='50GB')
        mock_tenant.assert_called_once_with()
        mock_tenant.return_value.volumes.create.assert_called_once_with(size=50, volume_type=None,
            name=None, imageRef=None, description=None)
        self.assertTrue(isinstance(volume, volumes.Volume))

    @patch.object(CinderWrapper, 'get')
    def test_no_volume_is_ready(self, mock_get):
        self.assertRaises(AiToolsCinderError, self.tenant.is_ready, volume_id=None)
        self.assertFalse(mock_get.called)

    @patch.object(CinderWrapper, 'get', return_value=Mock(spec=volumes.Volume, id=1,
        status='available', bootable='true'))
    def test_volume_ready_is_ready(self, mock_get):
        volume_id = 1
        result_volume = self.tenant.is_ready(volume_id)
        self.assertTrue(isinstance(result_volume, volumes.Volume))
        self.assertTrue(volume_id == result_volume.id)
        mock_get.assert_called_once_with(volume_id)

    @patch.object(CinderWrapper, 'get', return_value=Mock(spec=volumes.Volume, id=1,
        status='creating', bootable='false'))
    def test_timeout_creating_is_ready(self, mock_get):
        volume_id = 1
        self.assertRaises(AiToolsCinderError, self.tenant.is_ready, volume_id, wait_time=1, timeout=1)
        self.assertTrue(mock_get.called >= 1)

    @patch.object(CinderWrapper, 'get', return_value=Mock(spec=volumes.Volume, id=1,
        status='downloading', size=1))
    def test_timeout_downloading_is_ready(self, mock_get):
        volume_id = 1
        self.assertRaises(AiToolsCinderError, self.tenant.is_ready, volume_id, wait_time=1, timeout=1)
        self.assertTrue(mock_get.called >= 1)

    @patch.object(CinderWrapper, 'get', return_value=Mock(spec=volumes.Volume, id=1,
        status='available', bootable='false', size=1))
    def test_volume_nonbootable_bootable_required_is_ready(self, mock_get):
        volume_id = 1
        self.assertRaises(AiToolsCinderError, self.tenant.is_ready, volume_id,
            needs_to_be_bootable=True)
        mock_get.assert_called_once_with(volume_id)

    @patch.object(CinderWrapper, 'get', return_value=Mock(spec=volumes.Volume, id=1,
        status='available', bootable='false', size=1))
    def test_volume_nonbootable_is_ready(self, mock_get):
        volume_id = 1
        result_volume = self.tenant.is_ready(volume_id)
        self.assertTrue(isinstance(result_volume, volumes.Volume))
        self.assertTrue(volume_id == result_volume.id)
        mock_get.assert_called_once_with(volume_id)

    @patch.object(CinderWrapper, 'get', return_value=Mock(spec=volumes.Volume, id=1,
        status='in-use', bootable='true', size=1))
    def test_volume_inuse_is_ready(self, mock_get):
        volume_id = 1
        self.assertRaises(AiToolsCinderError, self.tenant.is_ready, volume_id)
        mock_get.assert_called_once_with(volume_id)

    @patch.object(CinderWrapper, 'get', side_effect=AiToolsCinderError)
    def test_ai_tools_exception_ready_to_boot(self, mock_get):
        volume_id = 1
        self.assertRaises(AiToolsCinderError, self.tenant.is_ready, volume_id,
            wait_time=1)
        mock_get.assert_called_once_with(volume_id)

    @patch.object(CinderWrapper, 'get', side_effect=Exception)
    def test_exception_ready_to_boot(self, mock_get):
        volume_id = 1
        try:
            self.tenant.is_ready(volume_id, wait_time=1)
        except AiToolsCinderError:
            self.fail("It shouldn't be an AiToolsCinderError")
        except Exception:
            mock_get.assert_called_once_with(volume_id)
        else:
            self.fail("It should throw an exception")

    @patch.object(CinderWrapper, 'get', side_effect=[Mock(spec=volumes.Volume, id=1, status='creating',
        bootable='false', size=1), Mock(spec=volumes.Volume, id=1, status='downloading', bootable='false', size=1),
        Mock(spec=volumes.Volume, id=1, status='available', bootable='true', size=1)])
    def test_wait_and_is_ready(self, mock_get):
        volume_id = 1
        result_volume = self.tenant.is_ready(volume_id, wait_time=1)
        self.assertTrue(len(mock_get.mock_calls) == 3)
        self.assertTrue(isinstance(result_volume, volumes.Volume))
        self.assertTrue(result_volume.id == 1)
        self.assertTrue(result_volume.status == 'available')
        self.assertTrue(result_volume.bootable == 'true')

    @patch.object(CinderWrapper, 'get', side_effect=[Mock(spec=volumes.Volume, id=1, status='creating',
        bootable='false', size=1), Mock(spec=volumes.Volume, id=1, status='downloading', bootable='false', size=1),
        Mock(spec=volumes.Volume, id=1, status='in-use', bootable='true', size=1)])
    def test_wait_and_is_inuse_ready_to_boot(self, mock_get):
        volume_id = 1
        self.assertRaises(AiToolsCinderError, self.tenant.is_ready, volume_id, wait_time=1)
        self.assertTrue(len(mock_get.mock_calls) == 3)

