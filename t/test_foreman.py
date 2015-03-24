import unittest
import sys
import os
import re
import requests
import json
import urllib

from mock import Mock, patch, ANY, call

from aitools.foreman import ForemanClient
from aitools.httpclient import HTTPClient
from aitools.errors import AiToolsForemanError
from aitools.errors import AiToolsForemanNotAllowedError
from aitools.errors import AiToolsForemanNotFoundError

TEST_HOST='localhost'
TEST_PORT=1

def generate_response(code, payload, meta = False, page=1, page_size=3, subtotal=1):
    response = Mock()
    response.headers = {}
    if meta:
        payload = {'results': payload}
        # This is the count of total matches
        payload['subtotal'] = subtotal
        # This is the count of total resources for a particular model
        payload['total'] = 1
        # The current page
        payload['page'] = 1
        # The page size
        payload['per_page'] = page_size
    if isinstance(payload, str):
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

    #### GENERIC RESOLVERS ####

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK,
            [{"name":"production","id":16,"created_at":"Z","updated_at":"Z"}],
            meta=True))
    def test_resolve_model_id(self, mock_client):
        self.client._ForemanClient__resolve_model_id("environment", "production")
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get',
                full_uri("environments/?search=%s&page=1" %
                    urllib.quote('name="production"')), ANY, None)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK, [], meta=True))
    def test_resolve_model_id_nothing_found(self, mock_client):
        self.assertRaises(AiToolsForemanNotFoundError,\
            self.client._ForemanClient__resolve_model_id,
            "foo", "noluck")
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get',
                full_uri("foos/?search=%s&page=1" %
                    urllib.quote('name="noluck"')), ANY, None)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK,
            {"name":"production","id":16}, meta=False))
    def test_resolve_model(self, mock_client):
        result = self.client._ForemanClient__resolve_model("environment", 2)
        self.assertEquals(result, {"name":"production","id":16})
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get', full_uri("environments/2"), ANY, None)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK,
            [{"name":"production","id":16,"full":"production 1"},
            {"name":"production","id":17,"full":"production 2"}],
            meta=True))
    def test_resolve_model_id_multiple_results(self, mock_client):
        self.assertRaises(AiToolsForemanError,\
            self.client._ForemanClient__resolve_model_id,
            "environment", "production")
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get',
                full_uri("environments/?search=%s&page=1" %
                    urllib.quote('name="production"')), ANY, None)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK,
            [{"name":"production","id":16,"full":"production_1"},
            {"name":"production","id":17,"full":"production_2"}],
            meta=True))
    def test_resolve_model_id_multiple_results_with_filter(self, mock_client):
        idd =self.client._ForemanClient__resolve_model_id("environment",
            "production", results_filter=lambda x: x['full'] == "production_1")
        self.assertEquals(idd, 16)
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get',
                full_uri("environments/?search=%s&page=1" %
                    urllib.quote('name="production"')), ANY, None)

    #### SEARCH_QUERY ####

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK,
                [],
                meta=True, page=1, page_size=5, subtotal=0),
        ])
    def test_resolve_search_query_no_results(self, mock_client):
        model = "foomodel"
        query = 'name="production"'
        results = self.client.search_query(model, query)
        self.assertEquals(results, [])
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('get', full_uri("%s/?search=%s&page=1" %
                    (model, urllib.quote(query))), ANY, None)])

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK,
                [{"name":"foo","id":1,"created_at":"Z","updated_at":"Z"},
                {"name":"bar","id":2,"created_at":"Z","updated_at":"Z"}],
                meta=True, page=1, page_size=2, subtotal=2),
        ])
    def test_resolve_search_query_single_page(self, mock_client):
        model = "foomodel"
        query = 'name="production"'
        results = self.client.search_query(model, query)
        self.assertEquals(len(results), 2)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('get', full_uri("%s/?search=%s&page=1" %
                    (model, urllib.quote(query))), ANY, None)])

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK,
                [{"name":"foo","id":1,"created_at":"Z","updated_at":"Z"},
                {"name":"bar","id":2,"created_at":"Z","updated_at":"Z"}],
                meta=True, page=1, page_size=2, subtotal=3),
            generate_response(requests.codes.OK,
                [{"name":"baz","id":16,"created_at":"Z","updated_at":"Z"}],
                meta=True, page=2, page_size=2, subtotal=3)
        ])
    def test_resolve_search_query_multiple_pages(self, mock_client):
        model = "foomodel"
        query = 'name="production"'
        results = self.client.search_query(model, query)
        self.assertEquals(len(results), 3)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('get', full_uri("%s/?search=%s&page=1" %
                    (model, urllib.quote(query))), ANY, None),
            call('get', full_uri("%s/?search=%s&page=2" %
                    (model, urllib.quote(query))), ANY, None)])

    #### SPECIFIC RESOLVERS ####

    @patch.object(ForemanClient, '_ForemanClient__resolve_model_id',
        return_value=1)
    def test_resolve_environment_id(self, mock_client):
        result = self.client._ForemanClient__resolve_environment_id("foo")
        self.assertEquals(result, 1)
        self.client._ForemanClient__resolve_model_id.\
            was_called_once_with("foo")

    @patch.object(ForemanClient, '_ForemanClient__resolve_model_id',
        return_value=1)
    def test_resolve_hostgroup_id(self, mock_client):
        result = self.client._ForemanClient__resolve_hostgroup_id("foo")
        self.assertEquals(result, 1)
        self.client._ForemanClient__resolve_model_id.\
            was_called_once_with("hostgroup", "foo", search_key='label')

    @patch.object(HTTPClient, 'do_request', return_value=
            generate_response(requests.codes.OK,
            [{"id": 1,"name":"Foo","major":"6","minor":"4","fullname":"Foo 6.4"},
            {"id": 2,"name":"Foo","major":"6","minor":"3","fullname":"Foo 6.31"}],
            meta=True, page=1, page_size=5, subtotal=2))
    def test_resolve_operatingsystem_id(self, mock_client):
        result = self.client._ForemanClient__resolve_operatingsystem_id("Foo 6.31")
        self.assertEquals(result, 2)
        self.assertRaises(AiToolsForemanError,
            self.client._ForemanClient__resolve_operatingsystem_id,
            "Foodsfds")

    @patch.object(HTTPClient, 'do_request', return_value=
            generate_response(requests.codes.OK,
            [{"id": 3,"name":"Foo"}],
            meta=True, page=1, page_size=5, subtotal=1))
    def test_resolve_medium_id(self, mock_client):
        query = 'name="Foo"'
        result = self.client._ForemanClient__resolve_medium_id("Foo")
        self.assertEquals(result, 3)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('get', full_uri("media/?search=%s&page=1" %
                    urllib.quote(query)), ANY, None)])

    #### ADDHOST ####

    @patch.object(ForemanClient, '_ForemanClient__resolve_environment_id',
        return_value=1)
    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        return_value=2)
    @patch.object(ForemanClient, '_ForemanClient__resolve_user_id',
        return_value=3)
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK, []))
    def test_addhost_unmanaged(self, *args):
        self.client.addhost(fqdn='foo.cern.ch',
            environment='foo',
            hostgroup='bar/baz',
            owner='bob')
        self.client._ForemanClient__resolve_environment_id.\
            was_called_once_with("foo")
        self.client._ForemanClient__resolve_hostgroup_id.\
            was_called_once_with("bar/baz")
        self.client._ForemanClient__resolve_user_id.\
            was_called_once_with("bob")
        expected_payload = {'name': 'foo.cern.ch',
            'environment_id': 1,
            'hostgroup_id': 2,
            'owner_id': 3,
            'owner_type': 'User',
            'managed': False}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("hosts"), ANY,
                json.dumps(expected_payload))

    @patch.object(ForemanClient, '_ForemanClient__resolve_environment_id',
        return_value=1)
    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        return_value=2)
    @patch.object(ForemanClient, '_ForemanClient__resolve_user_id',
        return_value=3)
    @patch.object(ForemanClient, '_ForemanClient__resolve_operatingsystem_id',
        return_value=4)
    @patch.object(ForemanClient, '_ForemanClient__resolve_medium_id',
        return_value=5)
    @patch.object(ForemanClient, '_ForemanClient__resolve_architecture_id',
        return_value=6)
    @patch.object(ForemanClient, '_ForemanClient__resolve_ptable_id',
        return_value=7)
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK, []))
    def test_addhost_managed(self, *args):
        self.client.addhost(fqdn='foo.cern.ch',
            environment='foo',
            hostgroup='bar/baz',
            owner='bob',
            managed=True,
            operatingsystem="Foo 5.6",
            medium="Foo",
            architecture="Foo arch",
            comment="baaar",
            ptable="Ptable",
            mac="foomac",
            ip="fooip")
        self.client._ForemanClient__resolve_environment_id.\
            was_called_once_with("foo")
        self.client._ForemanClient__resolve_hostgroup_id.\
            was_called_once_with("bar/baz")
        self.client._ForemanClient__resolve_user_id.\
            was_called_once_with("bob")
        self.client._ForemanClient__resolve_operatingsystem_id.\
            was_called_once_with("Foo 5.6")
        self.client._ForemanClient__resolve_medium_id.\
            was_called_once_with("Foo")
        self.client._ForemanClient__resolve_architecture_id.\
            was_called_once_with("Foo arch")
        self.client._ForemanClient__resolve_ptable_id.\
            was_called_once_with("Ptable")
        expected_payload = {'name': 'foo.cern.ch',
            'environment_id': 1,
            'hostgroup_id': 2,
            'owner_id': 3,
            'owner_type': 'User',
            'operatingsystem_id': 4,
            'medium_id': 5,
            'architecture_id': 6,
            'ptable_id': 7,
            'comment': 'baaar',
            'ip': 'fooip',
            'mac': 'foomac',
            'managed': True}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("hosts"), ANY, ANY)

    @patch.object(ForemanClient, '_ForemanClient__resolve_environment_id',
        return_value=1)
    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        return_value=2)
    @patch.object(ForemanClient, '_ForemanClient__resolve_user_id',
        return_value=3)
    @patch.object(ForemanClient, '_ForemanClient__resolve_operatingsystem_id',
        return_value=4)
    @patch.object(ForemanClient, '_ForemanClient__resolve_medium_id',
        return_value=5)
    @patch.object(ForemanClient, '_ForemanClient__resolve_architecture_id',
        return_value=6)
    @patch.object(ForemanClient, '_ForemanClient__resolve_ptable_id',
        return_value=7)
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK, []))
    def test_addhost_unmanaged_fails_if_missing_fields_and_managed(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.addhost,
            fqdn='foo.cern.ch',
            environment='foo',
            hostgroup='bar/baz',
            owner='bob',
            managed=True)

    #### UPDATEHOST ####

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        return_value=2)
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK, []))
    def test_updatehost_single_field(self, *args):
        self.client.updatehost(fqdn='foo.cern.ch',
            hostgroup='bar/baz')
        self.client._ForemanClient__resolve_hostgroup_id.\
            was_called_once_with("bar/baz")
        expected_payload = {'hostgroup_id': 2}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, json.dumps(expected_payload))

    @patch.object(ForemanClient, '_ForemanClient__resolve_environment_id',
        return_value=6)
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.NOT_FOUND, []))
    def test_updatehost_not_found(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.updatehost,
            fqdn='foo.cern.ch', environment='foo1')
        self.client._ForemanClient__resolve_environment_id.\
            was_called_once_with("foo1")
        expected_payload = {'environment_id': 6}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, json.dumps(expected_payload))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.UNPROCESSABLE_ENTITY,
            {'error': {'full_messages': ['MAC not valid']}}))
    def test_updatehost_bad_data(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.updatehost,
            fqdn='foo.cern.ch', mac='foo1')
        expected_payload = {'mac': 'foo1'}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, json.dumps(expected_payload))


    #### GETHOST ####

    @patch.object(ForemanClient, '_ForemanClient__resolve_model',
        return_value={"name":"production","id":16})
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK,
              {
                "parameters": [
                  {
                    "id": 22070,
                    "name": "foo",
                    "value": "true"
                  }
                ],
                "created_at": "2013-07-19T10:50:41Z",
                "ip": "128.142.201.152",
                "id": 10865,
                "operatingsystem_name": "SLC 6.6",
                "updated_at": "2015-03-10T15:09:34Z",
                "managed": False,
                "hostgroup_name": "playground/ibarrien/dev",
                "model_id": 408,
                "comment": "",
                "environment_id": 55937,
                "provision_method": "build",
                "owner_type": "User",
                "hostgroup_id": 377,
                "domain_id": 1,
                "mac": "02:16:3e:00:a1:4f",
                "name": "foo.cern.ch",
                "owner_id": 54,
                "architecture_name": "x86_64",
                "model_name": "OpenStack Nova",
                "domain_name": "cern.ch",
                "last_compile": "2015-03-10T15:07:50Z",
                "operatingsystem_id": 51,
                "certname": "nachodev03.cern.ch",
                "enabled": True,
                "architecture_id": 1,
                "last_report": "2015-03-10T15:07:43Z",
                "environment_name": "qa"
              }
            ))
    def test_gethost(self, *args):
        self.client.gethost(fqdn='foo.cern.ch',
            toexpand=['hostgroup'])
        self.client._ForemanClient__resolve_model.\
            was_called_once_with("hostgroup", 37)
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get', full_uri("hosts/foo.cern.ch"), ANY, ANY)

    #### DELHOST ####

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
