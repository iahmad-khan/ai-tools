import unittest
import sys
import os
import re
import requests
import json

from mock import Mock, patch, ANY

from aitools.foreman import ForemanClient
from aitools.httpclient import HTTPClient
from aitools.errors import AiToolsForemanError
from aitools.errors import AiToolsForemanNotAllowedError
from aitools.errors import AiToolsForemanNotFoundError

TEST_HOST='localhost'
TEST_PORT=1

def generate_response(code, payload):
    response = Mock()
    response.headers = {}
    if type(payload) == str:
        response.text = payload
        response.headers['content-type'] = 'text/html'
    else:
        response.text = json.dumps(payload)
        response.headers['content-type'] = 'application/json'
    response.json = Mock(return_value=payload)
    return (code, response)

def full_uri(path):
    return "https://%s:%s/api/%s" % (TEST_HOST, TEST_PORT, path)

class TestForemanClient(unittest.TestCase):

    def setUp(self):
        self.client = ForemanClient(host=TEST_HOST, port=TEST_PORT, timeout=1)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK, {}))
    def test_delhost_existing(self, mock_client):
        self.client.delhost('foo.cern.ch')
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('delete', full_uri('hosts/foo.cern.ch'), ANY, None)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.NOT_FOUND, "rubbish"))
    def test_delhost_notfound(self, mock_client):
        self.assertRaises(AiToolsForemanNotFoundError, self.client.delhost, 'foo.cern.ch')
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('delete', full_uri('hosts/foo.cern.ch'), ANY, None)
