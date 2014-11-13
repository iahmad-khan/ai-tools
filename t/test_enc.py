import unittest
import requests
from mock import Mock, patch

from aitools.enc import EncClient
from aitools.httpclient import HTTPClient
from aitools.errors import AiToolsEncError

class TestEnc(unittest.TestCase):

    def setUp(self):
        self.enc = EncClient(host='none.cern.ch', port=1, timeout=1)

    @patch.object(HTTPClient, 'do_request',
        return_value=[requests.codes.ok, Mock(text="{'foo': 'bar'}")])
    def test_ok(self, mock_get):
        (code, classification) = self.enc.get_node_enc('foo.cern.ch')
        self.assertEquals(classification['foo'], 'bar')

    @patch.object(HTTPClient, 'do_request',
        return_value=[requests.codes.not_found, Mock(text="Fail")])
    def test_notfound(self, mock_get):
        self.assertRaises(AiToolsEncError, self.enc.get_node_enc, 'foo.cern.ch')

    @patch.object(HTTPClient, 'do_request',
        return_value=[requests.codes.unauthorized, Mock(text="Fail")])
    def test_noaccess(self, mock_get):
        self.assertRaises(AiToolsEncError, self.enc.get_node_enc, 'foo.cern.ch')
        mock_get.return_value=[requests.codes.forbidden, Mock(text="Fail")]
        self.assertRaises(AiToolsEncError, self.enc.get_node_enc, 'foo.cern.ch')

    @patch.object(HTTPClient, 'do_request',
        return_value=[requests.codes.precondition_failed, Mock(text="Fail")])
    def test_computation_failure(self, mock_get):
        self.assertRaises(AiToolsEncError, self.enc.get_node_enc, 'foo.cern.ch')
