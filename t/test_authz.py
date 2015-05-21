__author__ = "ahencz"

import os
import sys
sys.path.insert(0, os.path.abspath("../src"))
import unittest
from mock import Mock, patch
import requests
import json
from aitools.httpclient import HTTPClient
from argparse import ArgumentParser
from aitools.config import AuthzConfig
from aitools.authz import AuthzClient
from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsAuthzError
from aitools.errors import AiToolsAuthzNotAllowedError
from aitools.errors import AiToolsAuthzNotFoundError
from aitools.errors import AiToolsAuthzInternalServerError
from aitools.errors import AiToolsAuthzNotImplementedError

# Test cases were based on Tbag tests

class TestAuthz(unittest.TestCase):

    # ugly global variable to be used by the decorators
    my_test_json_response = '{"valid": "json"}'

    def setUp(self):
        self.authz_config = AuthzConfig(configfile=os.path.abspath("ai.conf"))
        parser = ArgumentParser()
        self.authz_config.add_standard_args(parser)
        (pargs, _) = self.authz_config.parser.parse_known_args()
        self.authz_config.read_config_and_override_with_pargs(pargs)
        self.test_entities = { "hostgroup": "punch/puppetdb", "hostname": "ahencz-dev" }
        self.test_user = 'ahencz'
        self.authz_config.read_config_and_override_with_pargs(pargs)
        self.client = AuthzClient()
        # self.test_ownership = [["ahencz@cerN.ch ", "ai-config-team"], ["ai-robots@CERN.CH"]]
        # self.test_options = { "hasPhysical": True }

# Regular unit tests for the one single function the lib

    # __do_api_request

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.OK, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_OK(self, mock_response):
        result = self.client._AuthzClient__do_api_request('get','someurl')
        self.assertTrue(isinstance(result,tuple))
        self.assertEqual(200, result[0])
        self.assertEqual(mock_response()[1].text, result[1])

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.forbidden, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_forbidden(self, mock_response):
        self.assertRaises(AiToolsAuthzNotAllowedError, self.client._AuthzClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.unauthorized, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_unauthorized(self, mock_response):
        self.assertRaises(AiToolsAuthzNotAllowedError, self.client._AuthzClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', side_effect=AiToolsHTTPClientError)
    def test_api_request_clienterror(self, mock_response):
        self.assertRaises(AiToolsAuthzError, self.client._AuthzClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.not_implemented, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_notimplemented(self, mock_response):
        self.assertRaises(AiToolsAuthzNotImplementedError, self.client._AuthzClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.internal_server_error, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_itnernalserverrror(self, mock_response):
        self.assertRaises(AiToolsAuthzInternalServerError, self.client._AuthzClient__do_api_request, 'get', 'someurl')

    # get_authz

    @patch.object(AuthzClient, '_AuthzClient__do_api_request', return_value=(requests.codes.OK, my_test_json_response))
    def test_get_authz_ok(self, mock_response):
        response = self.client.get_authz(self.test_entities['hostgroup'], 'hostgroup', self.test_user)
        self.assertEqual(response, mock_response()[1])

    @patch.object(AuthzClient, '_AuthzClient__do_api_request', side_effect=AiToolsAuthzError)
    def test_get_authz_exception(self, mock_response):
        self.assertRaises(AiToolsAuthzError, self.client.get_authz, self.test_entities['hostgroup'], 'hostgroup', self.test_user)

    @patch.object(AuthzClient, '_AuthzClient__do_api_request', return_value=(requests.codes.not_found, my_test_json_response))
    def test_get_authz_notfound(self, mock_response):
        self.assertRaises(AiToolsAuthzNotFoundError, self.client.get_authz, self.test_entities['hostgroup'], 'hostgroup', self.test_user)

    @patch.object(AuthzClient, '_AuthzClient__do_api_request', return_value=(requests.codes.OK, my_test_json_response))
    def test_get_authz_invalid_args(self, mock_response):
        self.assertRaises(AttributeError, self.client.get_authz, self.test_entities['hostgroup'], None, self.test_user)
        self.assertRaises(AttributeError, self.client.get_authz, None, 'hostgroup', self.test_user)
        self.assertRaises(AttributeError, self.client.get_authz, self.test_entities['hostgroup'], 'hostgroup', None)



# Function like tests using the test service

    def test_00_default_args(self):
        self.assertEqual(self.authz_config.authz_hostname, "teigitest.cern.ch")

    def test_01_authz_get_info(self):
        authz = AuthzClient()

        scope = 'hostgroup'
        entity = self.test_entities[scope]
        # set_trace()
        resp = authz.get_authz(entity, scope, self.test_user)
        self.assertTrue(resp['authorized'])

        scope = 'hostname'
        entity = self.test_entities[scope]
        resp = authz.get_authz(entity, scope, self.test_user)
        self.assertTrue(resp['authorized'])

    def test_02_authz_get_info_fail(self):
        authz = AuthzClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        requestor = self.test_user
        #Missing requestor
        self.assertRaises(TypeError, authz.get_authz, entity, scope)
        #None reuqestor
        self.assertRaises(AttributeError, authz.get_authz, entity, scope, None)
        #Nonexistent entity
        self.assertRaises(AiToolsAuthzNotAllowedError, authz.get_authz, 'idontexist', scope, requestor)
        #Unauthorized entity
        self.assertRaises(AiToolsAuthzNotAllowedError, authz.get_authz, 'afssrv', scope, requestor)
