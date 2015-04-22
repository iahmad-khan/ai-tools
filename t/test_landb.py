import unittest
import suds

from mock import Mock, patch, ANY, call

from aitools.landb import LandbClient
from aitools.errors import AiToolsLandbError
from aitools.errors import AiToolsLandbInitError

TEST_HOST="127.0.0.1"
TEST_PORT=1
TEST_USER="foo"
TEST_PASS="bar"

class DeviceInfo():
    pass

class PersonInput():
    pass

class TestLandbClient(unittest.TestCase):

    def setUp(self):
        self.sudsc_mock = patch('suds.client.Client').start()
        self.sudsc_mock.return_value.service.getAuthToken.return_value = 2
        self.client = LandbClient(TEST_USER, TEST_PASS,
            host=TEST_HOST, port=TEST_PORT)
        self.sudsc_mock.return_value.service.getAuthToken.assert_called_once_with(TEST_USER,
            TEST_PASS, 'CERN')
        self.sudsc_mock.return_value.set_options.assert_called_once()

    def prepare_mock_for_device_update(self):
        current = DeviceInfo()
        current.ResponsiblePerson = PersonInput()
        current.ResponsiblePerson.Name = "BAR"
        current.ResponsiblePerson.FirstName = "E-GROUP"
        self.sudsc_mock.return_value.service.getDeviceInfo.return_value = current
        self.sudsc_mock.return_value.factory.create.return_value = PersonInput()

    def test_change_responsible_egroup_success(self):
        self.client.change_responsible("foo.cern.ch", "foo", None)
        self.sudsc_mock.return_value.service.deviceUpdate.is_called_once_with("foo", ANY)
        update_args = self.sudsc_mock.return_value.service.deviceUpdate.call_args_list
        self.assertEqual(1, len(update_args))
        actual_new_device = update_args[0][0][1]
        self.assertEqual("FOO", actual_new_device.ResponsiblePerson.Name)
        self.assertEqual("E-GROUP", actual_new_device.ResponsiblePerson.FirstName)

    def test_change_responsible_person_success(self):
        self.client.change_responsible("foo.cern.ch", "foo", "bar")
        self.sudsc_mock.return_value.service.deviceUpdate.is_called_once_with("foo", ANY)
        update_args = self.sudsc_mock.return_value.service.deviceUpdate.call_args_list
        self.assertEqual(1, len(update_args))
        actual_new_device = update_args[0][0][1]
        self.assertEqual("FOO", actual_new_device.ResponsiblePerson.Name)
        self.assertEqual("BAR", actual_new_device.ResponsiblePerson.FirstName)

    def test_change_responsible_failure(self):
        self.sudsc_mock.return_value.service.deviceUpdate.side_effect = \
            suds.WebFault("foo", "bar")
        self.assertRaises(AiToolsLandbError, self.client.change_responsible,
            "foo.cern.ch", "foo", None)

    def test_dryrun_on_no_device_update_is_done(self):
        self.client.dryrun = True
        self.client.change_responsible("foo.cern.ch", "foo", None)
        self.assertTrue(self.sudsc_mock.return_value.service.getDeviceInfo.called)
        self.assertFalse(self.sudsc_mock.return_value.service.deviceUpdate.called)
