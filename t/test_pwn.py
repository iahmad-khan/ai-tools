__author__ = "ahencz"

import os
import sys
sys.path.insert(0, os.path.abspath("../src"))
import unittest
import json
import requests
from mock import Mock, patch
from argparse import ArgumentParser
from aitools.config import PwnConfig
from aitools.pwn import PwnClient
from aitools.httpclient import HTTPClient
from aitools.errors import AiToolsPwnNotAllowedError
from aitools.errors import AiToolsPwnNotFoundError
from aitools.errors import AiToolsPwnNotImplementedError
from aitools.errors import AiToolsPwnInternalServerError
from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsPwnError

# Test cases were based on Tbag tests

class TestPwn(unittest.TestCase):

    # ugly global variable to be used by the decorators
    my_test_json_response = '{"valid": "json"}'

    def setUp(self):
        self.pwn_config = PwnConfig(configfile=os.path.abspath("ai.conf"))
        parser = ArgumentParser()
        self.pwn_config.add_standard_args(parser)
        (pargs, _) = self.pwn_config.parser.parse_known_args()
        self.pwn_config.read_config_and_override_with_pargs(pargs)
        self.client = PwnClient()
        self.test_entities = { "hostgroup": "punch/puppetdb", "module": "my_module" }
        self.test_ownership = [["aHencz@cerN.ch ", "ai-config-team"], ["ai-robots@CERN.CH"]]
        self.test_ownership_clean = [["ahencz", "ai-config-team"], ["ai-robots"]]
        self.test_options = { "hasPhysical": True }

    # fetch_pwn_endpoint

    def test_pwn_fetch_endpoint_invalid_scopes(self):
        self.assertRaises(AttributeError, self.client.fetch_pwn_endpoint, scope='invalid' )
        self.assertRaises(AttributeError, self.client.fetch_pwn_endpoint, scope=None )

    def test_pwn_fetch_endpoint(self):
        url_template = "pwn/v1/%s/%s/"
        scope = 'module'
        entity = self.test_entities[scope]
        url = self.client.fetch_pwn_endpoint(scope=scope, entity=entity)
        self.assertEqual(url, url_template%(scope, entity))
        url = self.client.fetch_pwn_endpoint(scope=scope)
        self.assertEqual(url, (url_template%(scope,''))[:-1])
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        url = self.client.fetch_pwn_endpoint(scope=scope, entity=entity)
        self.assertEqual(url, url_template%(scope, entity.replace("/", "-"))    )
        url = self.client.fetch_pwn_endpoint(scope=scope)
        self.assertEqual(url, (url_template%(scope, ''))[:-1])

    # clean_owners

    def test_pwn_clean_owners(self):
        result = self.client.clean_owners(self.test_ownership[0])
        self.assertTrue(isinstance(result, list))
        self.assertEqual(result, self.test_ownership_clean[0])

    # __do_api_request

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.OK, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_OK(self, mock_response):
            result = self.client._PwnClient__do_api_request('get','someurl')
            self.assertTrue(isinstance(result,tuple))
            self.assertEqual(200, result[0])
            self.assertEqual(mock_response()[1].text, result[1])

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.forbidden, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_forbidden(self, mock_response):
            self.assertRaises(AiToolsPwnNotAllowedError, self.client._PwnClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.unauthorized, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_unauthorized(self, mock_response):
            self.assertRaises(AiToolsPwnNotAllowedError, self.client._PwnClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', side_effect=AiToolsHTTPClientError)
    def test_api_request_clienterror(self, mock_response):

            self.assertRaises(AiToolsPwnError, self.client._PwnClient__do_api_request, 'get', 'someurl')

    # get_ownership

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.OK, my_test_json_response))
    def test_get_ownership_ok(self, mock_response):
        response = self.client.get_ownership(self.test_entities['module'], 'module')
        self.assertEqual(response, mock_response()[1])

    @patch.object(PwnClient, '_PwnClient__do_api_request', side_effect=AiToolsPwnError)
    def test_get_ownership_exception(self, mock_response):
        self.assertRaises(AiToolsPwnError, self.client.get_ownership, self.test_entities['module'], 'module')

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.OK, my_test_json_response))
    def test_get_ownership_invalid_args(self, mock_response):
        self.assertRaises(AttributeError, self.client.get_ownership, self.test_entities['module'], None)
        self.assertRaises(AttributeError, self.client.get_ownership, None, 'module')

    # create_ownership

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.OK, my_test_json_response))
    def test_create_ownership_ok(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        response = self.client.create_ownership(entity, scope, owners)
        mock_request.assert_called_once_with('post', self.client.fetch_pwn_endpoint(scope='module'),
            data=json.dumps({"owners":self.client.clean_owners(owners), scope: entity }))
        self.assertEqual(response, self.my_test_json_response)

    def test_create_ownership_invalid_args(self):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AttributeError, self.client.create_ownership, None, scope, owners)
        self.assertRaises(AttributeError, self.client.create_ownership, entity, None, owners)
        self.assertRaises(AttributeError, self.client.create_ownership, entity, scope, None)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_found, my_test_json_response))
    def test_create_ownership_not_found(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotFoundError, self.client.create_ownership, entity, scope, owners)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_allowed, my_test_json_response))
    def test_create_ownership_not_allowed(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotAllowedError, self.client.create_ownership, entity, scope, owners)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_implemented, my_test_json_response))
    def test_create_ownership_not_imlemented(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotImplementedError, self.client.create_ownership, entity, scope, owners)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.internal_server_error, my_test_json_response))
    def test_create_ownership_internal_server_error(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnInternalServerError, self.client.create_ownership, entity, scope, owners)


    # put_ownership

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.OK, my_test_json_response))
    def test_put_ownership_ok(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        response = self.client.put_ownership(entity, scope, owners)
        mock_request.assert_called_once_with('put', self.client.fetch_pwn_endpoint(entity=entity, scope='module'),
            data=json.dumps({"owners":self.client.clean_owners(owners), scope: entity }))
        self.assertEqual(response, self.my_test_json_response)

    def test_put_ownership_invalid_args(self):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AttributeError, self.client.put_ownership, None, scope, owners)
        self.assertRaises(AttributeError, self.client.put_ownership, entity, None, owners)
        self.assertRaises(AttributeError, self.client.put_ownership, entity, scope, None)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_found, my_test_json_response))
    def test_put_ownership_not_found(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotFoundError, self.client.put_ownership, entity, scope, owners)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_allowed, my_test_json_response))
    def test_put_ownership_not_allowed(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotAllowedError, self.client.put_ownership, entity, scope, owners)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_implemented, my_test_json_response))
    def test_put_ownership_not_imlemented(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotImplementedError, self.client.put_ownership, entity, scope, owners)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.internal_server_error, my_test_json_response))
    def test_put_ownership_internal_server_error(self, mock_request):
        owners = self.test_ownership[0]
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnInternalServerError, self.client.put_ownership, entity, scope, owners)

    # delete_ownership

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.OK, my_test_json_response))
    def test_delete_ownership_ok(self, mock_request):
        scope = 'module'
        entity = self.test_entities[scope]
        response = self.client.delete_ownership(entity, scope)
        mock_request.assert_called_once_with('delete', self.client.fetch_pwn_endpoint(entity=entity, scope='module'))
        self.assertEqual(response, self.my_test_json_response)

    def test_delete_ownership_invalid_args(self):
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AttributeError, self.client.delete_ownership, None, scope)
        self.assertRaises(AttributeError, self.client.delete_ownership, entity, None)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_found, my_test_json_response))
    def test_delete_ownership_not_found(self, mock_request):
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotFoundError, self.client.delete_ownership, entity, scope)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_allowed, my_test_json_response))
    def test_delete_ownership_not_allowed(self, mock_request):
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotAllowedError, self.client.delete_ownership, entity, scope)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.not_implemented, my_test_json_response))
    def test_delete_ownership_not_imlemented(self, mock_request):
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotImplementedError, self.client.delete_ownership, entity, scope)

    @patch.object(PwnClient, '_PwnClient__do_api_request', return_value=(requests.codes.internal_server_error, my_test_json_response))
    def test_delete_ownership_internal_server_error(self, mock_request):
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnInternalServerError, self.client.delete_ownership, entity, scope)

    # update_or_create_ownership

    @patch.object(PwnClient, 'get_ownership', return_value=my_test_json_response)
    @patch.object(PwnClient, 'put_ownership')
    def test_update_or_create_ownership_ok_update(self, mock_put, mock_get):
        scope = 'module'
        entity = self.test_entities[scope]
        owners = self.test_ownership[0]
        self.client.update_or_create_ownership(entity, scope, owners)
        mock_put.assert_called_once_with(entity, scope, owners, options=None)

    @patch.object(PwnClient, 'get_ownership', side_effect=AiToolsPwnNotFoundError)
    @patch.object(PwnClient, 'create_ownership')
    def test_update_or_create_ownership_ok_create(self, mock_put, mock_get):
        scope = 'module'
        entity = self.test_entities[scope]
        owners = self.test_ownership[0]
        self.client.update_or_create_ownership(entity, scope, owners)
        mock_put.assert_called_once_with(entity, scope, owners, options=None)

    # add_owners

    @patch.object(PwnClient, 'get_ownership', return_value={"owners": ["ai-admins"]})
    @patch.object(PwnClient, 'put_ownership')
    def test_add_owners_ok_add(self, mock_put, mock_get):
        scope = 'module'
        entity = self.test_entities[scope]
        new_owners = ['ai-config-team@CERN.cH ', 'aHencz']
        self.client.add_owners(entity, scope, new_owners)
        expected_owners = ['ai-admins', 'ai-config-team', 'ahencz' ]
        mock_put.assert_called_once_with(entity, scope, expected_owners, options=None)

    @patch.object(PwnClient, 'get_ownership', side_effect=AiToolsPwnNotFoundError)
    @patch.object(PwnClient, 'create_ownership')
    def test_add_owners_ok_new(self, mock_put, mock_get):
        scope = 'module'
        entity = self.test_entities[scope]
        new_owners = ['ai-config-team@CERN.cH ', 'aHencz']
        self.client.add_owners(entity, scope, new_owners)
        mock_put.assert_called_once_with(entity, scope, new_owners, options=None)

    # remove_owners

    @patch.object(PwnClient, 'get_ownership', return_value={"owners": ["ai-admins", "ahencz"]})
    @patch.object(PwnClient, 'put_ownership')
    def test_remove_owners_ok_add(self, mock_put, mock_get):
        scope = 'module'
        entity = self.test_entities[scope]
        rem_owners = ['aHencz@cern.CH']
        self.client.remove_owners(entity, scope, rem_owners)
        expected_owners = ['ai-admins']
        mock_put.assert_called_once_with(entity, scope, expected_owners, options=None)


# TESTS USING THE TEST SERVICE BELOW

# yes, explicit order is frowned upon, but add/show/delete so...
    # def test_00_default_args(self):
    #     self.assertEqual(self.pwn_config.pwn_hostname, "teigitest.cern.ch")
    #
    # def test_01_pwn_add_hostgroup_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     owners = self.test_ownership[0]
    #     options = self.test_options
    #     pwn.update_or_create_ownership(entity, scope, owners, options=options)
    #
    # def test_02_pwn_get_hostgroup_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     expected_owners = pwn.clean_owners(self.test_ownership[0])
    #     expected_options = self.test_options
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
    #
    # def test_03_pwn_update_hostgroup_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     owners = self.test_ownership[1]
    #     options = self.test_options
    #     pwn.update_or_create_ownership(entity, scope, owners)
    #
    # def test_04_pwn_get_hostgroup_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     expected_owners = pwn.clean_owners(self.test_ownership[1])
    #     expected_options = self.test_options
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
    #
    # def test_05_pwn_add_hostgroup_owners(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     owners_to_add = self.test_ownership[0]
    #     expected_owners = pwn.clean_owners(self.test_ownership[1] + self.test_ownership[0])
    #     expected_options = self.test_options
    #     pwn.add_owners(entity, scope, owners_to_add)
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
    #
    # def test_06_pwn_remove_hostgroup_owner(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     owners_to_remove = self.test_ownership[0][1]
    #     expected_owners  = pwn.clean_owners(self.test_ownership[1] + [self.test_ownership[0][0]])
    #     expected_options = self.test_options
    #     pwn.remove_owners(entity, scope, owners_to_remove)
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
    #
    # def test_07_pwn_del_hostgroup_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     result = pwn.delete_ownership(entity, scope)
    #     self.assertRaises(AiToolsPwnNotFoundError, pwn.get_ownership, entity, scope)
    #
    # def test_08_pwn_remove_owner_from_nonexistent_hostgroup(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     self.assertRaises(AiToolsPwnNotFoundError, pwn.remove_owners, entity, scope,
    #         self.test_ownership[0])
    # # Now the sama with modules
    #
    # def test_11_pwn_add_module_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'module'
    #     entity = self.test_entities[scope]
    #     owners = self.test_ownership[0]
    #     options = self.test_options
    #     pwn.update_or_create_ownership(entity, scope, owners, options=options)
    #
    # def test_12_pwn_get_module_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'module'
    #     entity = self.test_entities[scope]
    #     expected_owners = pwn.clean_owners(self.test_ownership[0])
    #     expected_options = self.test_options
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
    #
    # def test_13_pwn_update_module_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'module'
    #     entity = self.test_entities[scope]
    #     owners = self.test_ownership[1]
    #     options = self.test_options
    #     pwn.update_or_create_ownership(entity, scope, owners)
    #
    # def test_14_pwn_get_module_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'module'
    #     entity = self.test_entities[scope]
    #     expected_owners = pwn.clean_owners(self.test_ownership[1])
    #     expected_options = self.test_options
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
    #
    # def test_15_pwn_add_module_owners(self):
    #     pwn = PwnClient()
    #     scope = 'module'
    #     entity = self.test_entities[scope]
    #     owners_to_add = self.test_ownership[0]
    #     expected_owners = pwn.clean_owners(self.test_ownership[1] + self.test_ownership[0])
    #     expected_options = self.test_options
    #     pwn.add_owners(entity, scope, owners_to_add)
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
    #
    # def test_16_pwn_remove_module_owner(self):
    #     pwn = PwnClient()
    #     scope = 'module'
    #     entity = self.test_entities[scope]
    #     owners_to_remove = self.test_ownership[0][1]
    #     expected_owners  = pwn.clean_owners(self.test_ownership[1] + [self.test_ownership[0][0]])
    #     expected_options = self.test_options
    #     pwn.remove_owners(entity, scope, owners_to_remove)
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
    #
    # def test_17_pwn_del_module_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'module'
    #     entity = self.test_entities[scope]
    #     result = pwn.delete_ownership(entity, scope)
    #     self.assertRaises(AiToolsPwnNotFoundError, pwn.get_ownership, entity, scope)
    #
    # def test_18_pwn_remove_owner_from_nonexistent_module(self):
    #     pwn = PwnClient()
    #     scope = 'module'
    #     entity = self.test_entities[scope]
    #     self.assertRaises(AiToolsPwnNotFoundError, pwn.remove_owners, entity, scope,
    #         self.test_ownership[0])
