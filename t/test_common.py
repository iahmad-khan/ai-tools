__author__ = 'Alberto Rodriguez Peon'

import unittest
import re
from aitools.common import is_valid_UUID
from aitools.common import generator_device_names
from aitools.common import is_valid_size_format

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
		for i in range(5000):
			device = gen.next()
			self.assertTrue(device != 'vda')
			self.assertTrue(device not in names)
			self.assertTrue(re.match(r'^vd[a-z]+$', device))
			names.add(device)

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
