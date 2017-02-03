__author__ = 'Alberto Rodriguez Peon'

import unittest
import re

from mock import MagicMock

from aitools.common import is_valid_UUID
from aitools.common import generator_device_names
from aitools.common import is_valid_size_format
from aitools.common import get_nova_image_id
from aitools.errors import AiToolsNovaError

IMAGE_ID = '389323ff-25ba-4994-af99-5fee5ab3aa76'

class TestCommon(unittest.TestCase):

    def test_is_valid_UUID_empty(self):
        self.assertFalse(is_valid_UUID(value=''))

    def test_is_valid_UUID_false(self):
        self.assertFalse(is_valid_UUID(value='94afe123-b1d4-4198-87fe-920d220d0fc9a'))

    def test_is_valid_UUID_true(self):
        self.assertTrue(is_valid_UUID(value='94afe123-b1d4-4198-87fe-920d220d0f9a'))

    def test_generator_device_names_first_5(self):
        gen = generator_device_names()
        self.assertTrue(gen.next() == 'vdb')
        self.assertTrue(gen.next() == 'vdc')
        self.assertTrue(gen.next() == 'vdd')
        self.assertTrue(gen.next() == 'vde')
        self.assertTrue(gen.next() == 'vdf')

    def test_generator_device_names_no_vda_and_duplicates(self):
        gen = generator_device_names()
        names = set()
        for i in range(24):
            device = gen.next()
            self.assertTrue(device != 'vda')
            self.assertTrue(device not in names)
            self.assertTrue(re.match(r'^vd[a-z]$', device))
            names.add(device)
        self.assertTrue(gen.next() == 'vdz')
        self.assertRaises(StopIteration, gen.next)

    def test_is_valid_size_format_empty(self):
        self.assertFalse(is_valid_size_format(''))

    def test_is_valid_size_format_number(self):
        self.assertFalse(is_valid_size_format('10'))

    def test_is_valid_size_format_0GB(self):
        self.assertFalse(is_valid_size_format('0GB'))

    def test_is_valid_size_format_0TB(self):
        self.assertFalse(is_valid_size_format('0TB'))

    def test_is_valid_size_format_GB(self):
        self.assertTrue(is_valid_size_format('10GB'))

    def test_is_valid_size_format_TB(self):
        self.assertTrue(is_valid_size_format('10TB'))

    def test_is_valid_size_format_gb(self):
        self.assertTrue(is_valid_size_format('10gb'))

    def test_is_valid_size_format_tb(self):
        self.assertTrue(is_valid_size_format('10tb'))

    def test_get_nova_image_id_with_latest_base_by_id(self):
        nova = MagicMock()
        self.assertTrue(get_nova_image_id(nova, IMAGE_ID) == IMAGE_ID)
        self.assertFalse(nova.find_image_by_name.called)
        self.assertFalse(nova.get_latest_image.called)

    def test_get_nova_image_id_with_latest_test_by_id(self):
        nova = MagicMock()
        self.assertTrue(get_nova_image_id(nova, IMAGE_ID, 'Test') == IMAGE_ID)
        self.assertFalse(nova.find_image_by_name.called)
        self.assertFalse(nova.get_latest_image.called)

    def test_get_nova_image_id_with_latest_base_by_name(self):
        nova = MagicMock()
        nova.find_image_by_name.return_value = IMAGE_ID
        self.assertTrue(get_nova_image_id(nova, 'My image') == IMAGE_ID)
        self.assertFalse(nova.get_latest_image.called)
        self.assertTrue(nova.find_image_by_name.called)

    def test_get_nova_image_id_with_latest_test_by_name(self):
        nova = MagicMock()
        nova.find_image_by_name.return_value = IMAGE_ID
        self.assertTrue(get_nova_image_id(nova, 'Mock image', 'Test') == IMAGE_ID)
        self.assertFalse(nova.get_latest_image.called)
        self.assertTrue(nova.find_image_by_name.called)

    def test_get_nova_image_id_with_latest_base(self):
        nova = MagicMock()
        nova.get_latest_image.return_value = IMAGE_ID
        self.assertTrue(get_nova_image_id(nova, 'slc5') == IMAGE_ID)
        self.assertTrue(get_nova_image_id(nova, 'slc6') == IMAGE_ID)
        self.assertTrue(get_nova_image_id(nova, 'cc7') == IMAGE_ID)
        self.assertFalse(nova.find_image_by_name.called)
        self.assertTrue(nova.get_latest_image.called)

    def test_get_nova_image_id_with_latest_test(self):
        nova = MagicMock()
        nova.get_latest_image.return_value = IMAGE_ID
        self.assertTrue(get_nova_image_id(nova, 'slc5', 'Test') == IMAGE_ID)
        self.assertTrue(get_nova_image_id(nova, 'slc6', 'Test') == IMAGE_ID)
        self.assertTrue(get_nova_image_id(nova, 'cc7', 'Test') == IMAGE_ID)
        self.assertFalse(nova.find_image_by_name.called)
        self.assertTrue(nova.get_latest_image.called)

    def test_get_nova_image_id_with_not_existing_image(self):
        nova = MagicMock()
        nova.get_latest_image.side_effect = AiToolsNovaError()
        self.assertRaises(AiToolsNovaError, get_nova_image_id, nova, 'slc5', 'test')
        self.assertRaises(AiToolsNovaError, get_nova_image_id, nova, 'slc6', 'test')
        self.assertRaises(AiToolsNovaError, get_nova_image_id, nova, 'cc7', 'test')
        self.assertFalse(nova.find_image_by_name.called)
        self.assertTrue(nova.get_latest_image.called)
