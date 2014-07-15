__author__ = 'Alberto Rodriguez Peon'

import unittest
from aitools.common import is_valid_UUID

class TestCommon(unittest.TestCase):

	def test_is_valid_UUID_empty(self):
		self.assertFalse(is_valid_UUID(value=''))

	def test_is_valid_UUID_false(self):
		self.assertFalse(is_valid_UUID(value='94afe123-b1d4-4198-87fe-920d220d0fc9a'))

	def test_is_valid_UUID_true(self):
		self.assertTrue(is_valid_UUID(value='94afe123-b1d4-4198-87fe-920d220d0f9a'))
