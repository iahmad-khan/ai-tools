import unittest
import requests
import json
import urllib

from mock import Mock, patch, ANY, call

from aitools.foreman import ForemanClient
from aitools.httpclient import HTTPClient
from aitools.errors import AiToolsForemanError
from aitools.errors import AiToolsForemanNotFoundError
from aitools.errors import AiToolsForemanNotAllowedError

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

def full_uri(path, api=True):
    prefix = "api/" if api else ""
    return "https://%s:%s/%s%s" % (TEST_HOST, TEST_PORT, prefix, path)

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
            [{"id": 2,"name":"Foo","major":"6","minor":"3","title":"Foo 6.31"}],
            meta=True, page=1, page_size=5, subtotal=1))
    def test_resolve_operatingsystem_id(self, mock_client):
        result = self.client._ForemanClient__resolve_operatingsystem_id("Foo 6.31")
        self.assertEquals(result, 2)

    @patch.object(HTTPClient, 'do_request', return_value=
            generate_response(requests.codes.OK,
            [],
            meta=True, page=1, page_size=5, subtotal=0))
    def test_resolve_operatingsystem_id_not_found(self, mock_client):
        self.assertRaises(AiToolsForemanNotFoundError,
            self.client._ForemanClient__resolve_operatingsystem_id,
            "Foodsfds")

    @patch.object(HTTPClient, 'do_request', return_value=
            generate_response(requests.codes.OK,
            [{"id": 2,"name":"Bar","major":"6","minor":"3","title":"Foo 6.31"}],
            meta=True, page=1, page_size=5, subtotal=1))
    def test_resolve_operatingsystem_id_name_not_in_title(self, mock_client):
        result = self.client._ForemanClient__resolve_operatingsystem_id("Foo 6.31")
        self.assertEquals(result, 2)

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
        return_value=generate_response(requests.codes.CREATED, []))
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
        expected_payload = {'host':{'name': 'foo.cern.ch',
            'environment_id': 1,
            'hostgroup_id': 2,
            'owner_id': 3,
            'owner_type': 'User',
            'managed': False}}
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
        return_value=generate_response(requests.codes.CREATED, []))
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
        return_value=generate_response(requests.codes.CREATED, []))
    def test_addhost_unmanaged_fails_if_missing_fields_and_managed(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.addhost,
            fqdn='foo.cern.ch',
            environment='foo',
            hostgroup='bar/baz',
            owner='bob',
            managed=True)

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
        return_value=generate_response(requests.codes.INTERNAL_SERVER_ERROR, ""))
    def test_addhost_unmanaged_fails_if_ise(self, *args):
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
        host_payload = {
          'name': 'foo.cern.ch',
          'environment_id': 1,
          'hostgroup_id': 1,
          'operatingsystem_id': 1,
          'medium_id': 1,
          'architecture_id': 1,
          'comment': '',
          'ptable_id': 1,
          'mac': 'aa:bb:cc:dd:ee:ff',
          'ip': '192.168.1.1',
        }
        self.client.updatehost(host=host_payload,
            hostgroup='bar/baz')
        self.client._ForemanClient__resolve_hostgroup_id.\
            was_called_once_with("bar/baz")
        host_payload['hostgroup_id'] = 2
        expected_payload = {'host': host_payload}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, ANY)
        call = super(ForemanClient,self.client).do_request.call_args
        returned_payload = json.loads(call[0][3])
        self.assertEqual(expected_payload, returned_payload)


    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        return_value=2)
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK, []))
    def test_updatehost_none_fields_not_sent_back(self, *args):
        host_payload = {
          'name': 'foo.cern.ch',
          'environment_id': 1,
          'hostgroup_id': 1,
          'operatingsystem_id': 1,
          'medium_id': 1,
          'architecture_id': 1,
          'comment': '',
          'ptable_id': 1,
          'mac': None,
          'ip': None,
        }
        self.client.updatehost(host=host_payload,
            hostgroup='bar/baz')
        self.client._ForemanClient__resolve_hostgroup_id.\
            was_called_once_with("bar/baz")
        host_payload['hostgroup_id'] = 2
        expected_payload = {'host': host_payload}
        del expected_payload['host']['mac']
        del expected_payload['host']['ip']
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, ANY)
        call = super(ForemanClient,self.client).do_request.call_args
        returned_payload = json.loads(call[0][3])
        self.assertEqual(expected_payload, returned_payload)

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        return_value=2)
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.OK, []))
    def test_updatehost_expected_field_not_present(self, *args):
        host_payload = {
          'name': 'foo.cern.ch',
          'environment_id': 1,
          'hostgroup_id': 1,
          'operatingsystem_id': 1,
          'medium_id': 1,
          'architecture_id': 1,
          'comment': '',
          'ptable_id': 1,
          'ip': None,
        }
        self.client.updatehost(host=host_payload,
            hostgroup='bar/baz')
        self.client._ForemanClient__resolve_hostgroup_id.\
            was_called_once_with("bar/baz")
        host_payload['hostgroup_id'] = 2
        expected_payload = {'host': host_payload}
        del expected_payload['host']['ip']
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, ANY)
        call = super(ForemanClient,self.client).do_request.call_args
        returned_payload = json.loads(call[0][3])
        self.assertEqual(expected_payload, returned_payload)

    @patch.object(ForemanClient, '_ForemanClient__resolve_environment_id',
        return_value=6)
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.NOT_FOUND, []))
    def test_updatehost_not_found(self, *args):
        host_payload = {
          'name': 'foo.cern.ch',
          'environment_id': 1,
          'hostgroup_id': 1,
          'operatingsystem_id': 1,
          'medium_id': 1,
          'architecture_id': 1,
          'comment': '',
          'ptable_id': 1,
          'mac': 'aa:bb:cc:dd:ee:ff',
          'ip': '192.168.1.1',
        }
        self.assertRaises(AiToolsForemanError, self.client.updatehost,
            host=host_payload, environment='foo1')
        self.client._ForemanClient__resolve_environment_id.\
            was_called_once_with("foo1")
        host_payload['environment_id'] = 6
        expected_payload = {'host': host_payload}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, ANY)
        call = super(ForemanClient,self.client).do_request.call_args
        returned_payload = json.loads(call[0][3])
        self.assertEqual(expected_payload, returned_payload)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.UNPROCESSABLE_ENTITY,
            {'error': {'full_messages': ['MAC not valid']}}))
    def test_updatehost_bad_data(self, *args):
        host_payload = {
          'name': 'foo.cern.ch',
          'environment_id': 1,
          'hostgroup_id': 1,
          'operatingsystem_id': 1,
          'medium_id': 1,
          'architecture_id': 1,
          'comment': '',
          'ptable_id': 1,
          'mac': 'aa:bb:cc:dd:ee:ff',
          'ip': '192.168.1.1',
        }
        self.assertRaises(AiToolsForemanError, self.client.updatehost,
            host=host_payload, mac='foo1')
        host_payload['mac'] = 'foo1'
        expected_payload = {'host': host_payload}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, ANY)
        call = super(ForemanClient,self.client).do_request.call_args
        returned_payload = json.loads(call[0][3])
        self.assertEqual(expected_payload, returned_payload)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.INTERNAL_SERVER_ERROR, ""))
    def test_updatehost_ise(self, *args):
        host_payload = {
          'name': 'foo.cern.ch',
          'environment_id': 1,
          'hostgroup_id': 1,
          'operatingsystem_id': 1,
          'medium_id': 1,
          'architecture_id': 1,
          'comment': '',
          'ptable_id': 1,
          'mac': 'aa:bb:cc:dd:ee:ff',
          'ip': '192.168.1.1',
        }
        self.assertRaises(AiToolsForemanError, self.client.updatehost,
            host=host_payload, mac='foo1')
        host_payload['mac'] = 'foo1'
        expected_payload = {'host': host_payload}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('put', full_uri("hosts/foo.cern.ch"),
                ANY, ANY)
        call = super(ForemanClient,self.client).do_request.call_args
        returned_payload = json.loads(call[0][3])
        self.assertEqual(expected_payload, returned_payload)

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

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.NOT_FOUND, ""))
    def test_gethost_not_found(self, *args):
        self.assertRaises(AiToolsForemanNotFoundError, self.client.gethost,
            'foo.cern.ch', toexpand=[''])
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get', full_uri("hosts/foo.cern.ch"), ANY, ANY)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.INTERNAL_SERVER_ERROR, ""))
    def test_gethost_not_ise(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.gethost,
            'foo.cern.ch', toexpand=[''])
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

    #### IPMI STUFF ####

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK,
                [{"name":"foo-ipmi.cern.ch","id":1,"type":"Nic::BMC",
                "provider": "IPMI"}],
                meta=True, page=1, page_size=5, subtotal=2),
        ])
    def test_get_ipmi_interface_id_ok(self, mock_client):
        results = self.client.get_ipmi_interface_id("foo.cern.ch")
        self.assertEquals(results, 1)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('get', full_uri("hosts/foo.cern.ch/interfaces"), ANY, None)])

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK,
                [],
                meta=True, page=1, page_size=5, subtotal=0),
        ])
    def test_get_ipmi_interface_id_empty(self, mock_client):
        results = self.client.get_ipmi_interface_id("foo.cern.ch")
        self.assertEquals(results, None)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('get', full_uri("hosts/foo.cern.ch/interfaces"), ANY, None)])

    #### PARAMETERS STUFF ####

    @patch.object(ForemanClient, '_ForemanClient__do_api_request',
        return_value=(requests.codes.unprocessable_entity, {"error": ""}))
    def test_addhostparameter(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.addhostparameter,
            'foo.cern.ch', 'foo', 'bar')

    @patch.object(ForemanClient, '_ForemanClient__do_api_request',
        return_value=(requests.codes.unprocessable_entity, {
                "error": {
                    "id": "null",
                    "full_messages": ["Name has already been taken"]
                }
        }))
    def test_addhostparameter_full_messages(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.addhostparameter,
            'foo.cern.ch', 'foo', 'bar')

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        return_value=2)
    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK,
                [{"name":"foo","id":1,"value":"bar"}],
                meta=True, page=1, page_size=5, subtotal=2),
        ])
    def test_gethostgroupparameters_ok(self, *args):
        results = self.client.gethostgroupparameters("hg/1")
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0]['name'], 'foo')
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('get', full_uri("hostgroups/2/parameters"), ANY, None)])

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        return_value=2)
    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK, [],
                meta=True, page=1, page_size=5, subtotal=0),
        ])
    def test_gethostgroupparameters_zero(self, *args):
        results = self.client.gethostgroupparameters("hg/1")
        self.assertEquals(len(results), 0)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('get', full_uri("hostgroups/2/parameters"), ANY, None)])

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK,
                {"name":"foo","id":1,"value":"bar"}, meta=False),
        ])
    def test_getaddhostparameter_ok(self, *args):
        self.client.addhostparameter('foo.cern.ch', 'a', 'b')
        expected = '{"parameter": {"name": "a", "value": "b"}}'
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('post', full_uri("hosts/foo.cern.ch/parameters"), ANY, expected)])

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.NOT_FOUND,
                {"error": {"message": "foo"}}, meta=False),
        ])
    def test_getaddhostparameter_host_not_found(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.addhostparameter,
            'foo.cern.ch', 'a', 'b')
        expected = '{"parameter": {"name": "a", "value": "b"}}'
        super(ForemanClient, self.client).do_request\
            .assert_has_calls([
            call('post', full_uri("hosts/foo.cern.ch/parameters"), ANY, expected)])

    #### GETKS ####

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.internal_server_error, []))
    def test_getks_uncontrolled_status_code(self, *args):
        fqdn = "foo.cern.ch"
        self.assertRaises(AiToolsForemanError, self.client.getks, fqdn=fqdn)
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get',
                full_uri("unattended/provision?hostname=%s" % fqdn, api=False), ANY, ANY)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.not_found, []))
    def test_getks_not_found(self, *args):
        fqdn = "foo.cern.ch"
        self.assertRaises(AiToolsForemanError, self.client.getks, fqdn=fqdn)
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get',
                full_uri("unattended/provision?hostname=%s" % fqdn, api=False), ANY, ANY)

    #### GETFACTS ####

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.internal_server_error, []))
    def test_getfacts_uncontrolled_status_code(self, *args):
        fqdn = "foo.cern.ch"
        self.assertRaises(AiToolsForemanError, self.client.getfacts, fqdn=fqdn)
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get',
                full_uri("hosts/%s/facts/?per_page=500" % fqdn), ANY, ANY)

    #### CREATEHOSTGROUP ####

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.unprocessable_entity, []))
    def test_createhostgroup_hg_exists_already(self, *args):
        hg = "foobar"
        self.assertRaises(AiToolsForemanNotAllowedError, self.client.createhostgroup,
            hostgroup=hg)

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.internal_server_error, []))
    def test_createhostgroup_uncontrolled_status_code(self, *args):
        hg = "foobar"
        self.assertRaises(AiToolsForemanError, self.client.createhostgroup,
            hostgroup=hg)
        expected_payload = {'hostgroup': {'name': hg}}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post',
                full_uri("hostgroups"), ANY, json.dumps(expected_payload))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.created, {"id": 111}))
    def test_create_top_level_hostgroup_success(self, *args):
        hg = "foobar"
        self.assertEquals(111, self.client.createhostgroup(hostgroup=hg))
        expected_payload = {'hostgroup': {'name': hg}}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post',
                full_uri("hostgroups"), ANY, json.dumps(expected_payload))

    def createhostgroup_nested_success_resolve(hg):
        if hg == 'playground':
            return 2

        raise AssertionError("You're not supposed to determine"
                             " id of this hostgroup '%s'" % hg)

    def createhostgroup_nested_success_request(*req):
        if json.loads(req[3])['hostgroup']['name'] == 'foobar':
            return generate_response(requests.codes.created, {"id": 111})

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=createhostgroup_nested_success_resolve)
    @patch.object(HTTPClient, 'do_request',
        side_effect=createhostgroup_nested_success_request)
    def test_createhostgroup_nested_success(self, *args):
        hg = "playground/foobar"
        self.assertEquals(111, self.client.createhostgroup(hostgroup=hg))
        expected_payload = {'hostgroup': {'name': "foobar", 'parent_id': 2}}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post',
                full_uri("hostgroups"), ANY, json.dumps(expected_payload))

    def createhostgroup_nested_without_parents_fail_resolve(hg):
        if hg == 'notexistingyet':
            raise AiToolsForemanNotFoundError

        raise AssertionError("You're not supposed to determine"
                             " id of this hostgroup '%s'" % hg)

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=createhostgroup_nested_without_parents_fail_resolve)
    def test_createhostgroup_nested_without_parents_fail(self, *args):
        hg = "notexistingyet/foobar"
        self.assertRaises(AiToolsForemanNotAllowedError, self.client.createhostgroup,
            hostgroup=hg)

    def createhostgroup_nested_with_parents_success_resolve(hg):
        if hg == 'notexistingyet':
            raise AiToolsForemanNotFoundError

        raise AssertionError("You are not allowed to determine id of hostgroup '%s'" % hg)

    def createhostgroup_nested_with_parents_success_request(*req):
        name = json.loads(req[3])['hostgroup']['name']
        if name == 'foobar':
            return generate_response(requests.codes.created, {"id": 222})
        elif name == 'notexistingyet':
            return generate_response(requests.codes.created, {"id": 111})

        raise AssertionError("You are not allowed to create hostgroup '%s'" % name)

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=createhostgroup_nested_with_parents_success_resolve)
    @patch.object(HTTPClient, 'do_request',
        side_effect=createhostgroup_nested_with_parents_success_request)
    def test_createhostgroup_nested_with_parents_success(self, *args):
        hg = "notexistingyet/foobar"

        self.assertEquals(222, self.client.createhostgroup(hostgroup=hg, parents=True))

        expected_payload = {'hostgroup': {'parent_id': 111, 'name': 'foobar'}}
        super(ForemanClient, self.client).do_request\
            .assert_any_call('post',
                full_uri("hostgroups"), ANY, json.dumps(expected_payload))

        expected_payload = {'hostgroup': {'name': 'notexistingyet'}}
        super(ForemanClient, self.client).do_request\
            .assert_any_call('post',
                full_uri("hostgroups"), ANY, json.dumps(expected_payload))


    def createhostgroup_nested_3_success_resolve(hg):
        if hg == 'foo':
            return 42
        if hg == 'foo/bar':
            return 73

        raise AiToolsForemanNotFoundError

    def createhostgroup_nested_3_success_request(*req):
        if json.loads(req[3])['hostgroup']['name'] == 'baz':
            return generate_response(requests.codes.created, {"id": 111})

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=createhostgroup_nested_3_success_resolve)
    @patch.object(HTTPClient, 'do_request',
        side_effect=createhostgroup_nested_3_success_request)
    def test_createhostgroup_nested_3_success(self, *args):
        hg = "foo/bar/baz"

        self.assertEquals(111, self.client.createhostgroup(hostgroup=hg, parents=False))

        expected_payload = {'hostgroup': {'parent_id': 73, 'name': 'baz'}}
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post',
                full_uri("hostgroups"), ANY, json.dumps(expected_payload))


    @patch.object(HTTPClient, 'do_request')
    def test_createhostgroup_dryrun(self, *args):
        hg = "foobar"
        self.client.dryrun = True
        self.assertEquals(None, self.client.createhostgroup(hostgroup=hg))
        super(ForemanClient, self.client).do_request\
            .assert_not_called()

    def createhostgroup_nested_dryrun_resolve(hg):
        if hg == 'playground':
            return 2

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=createhostgroup_nested_dryrun_resolve)
    @patch.object(HTTPClient, 'do_request')
    def test_createhostgroup_nested_dryrun(self, *args):
        hg = "playground/foobar"
        self.client.dryrun = True
        self.assertEquals(None, self.client.createhostgroup(hostgroup=hg))
        super(ForemanClient, self.client).do_request\
            .assert_not_called()

    #### DELHOSTGROUP ####

    def delhostgroup_success_no_hosts_resolve(hg):
        if hg == 'playground':
            return 42
        if hg == 'playground/foobar':
            return 73

        raise AiToolsForemanNotFoundError

    def delhostgroup_success_no_hosts_request(*req):
        if req[0] == 'delete':
            if req[1] == 'https://localhost:1/api/hostgroups/73':
                return generate_response(requests.codes.ok, {"name": "foobar"})

        raise AssertionError('Trying to delete not allowed hostgroup')

    def delhostgroup_success_no_hosts_search(*req):
        if req[0] == 'hosts':
            return []

        if req[0] == 'hostgroups':
            if req[1] == 'playground/foobar/':
                return []

        raise AssertionError("You are not allowed to determine %s of hostgroup '%s'" %
                             (req[0], req[1]))

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=delhostgroup_success_no_hosts_resolve)
    @patch.object(HTTPClient, 'do_request',
        side_effect=delhostgroup_success_no_hosts_request)
    @patch.object(ForemanClient, 'search_query',
        side_effect=delhostgroup_success_no_hosts_search)
    def test_delhostgroup_success_no_hosts(self, *args):
        hg = "playground/foobar"

        self.assertEquals('foobar', self.client.delhostgroup(hostgroup=hg))


    def delhostgroup_fail_with_hosts_resolve(hg):
        if hg == 'playground/foobar':
            return 73

        raise AssertionError('No other hostgroups ids should be tried to determine')

    def delhostgroup_fail_with_hosts_search(*req):
        if req[0] == 'hosts':
            if "playground/foobar" in req[1]:
                return [{"name": "host1"}, {"name": "host2"}]
            return []

        raise AssertionError("Not allowed request")

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=delhostgroup_fail_with_hosts_resolve)
    @patch.object(ForemanClient, 'search_query',
        side_effect=delhostgroup_fail_with_hosts_search)
    def test_delhostgroup_fail_with_hosts(self, *args):
        hg = "playground/foobar"

        self.assertRaises(AiToolsForemanNotAllowedError, self.client.delhostgroup,
            hostgroup=hg)

    def delhostgroup_with_children_resolve(hg):
        if hg == 'playground':
            return 42
        if hg == 'playground/foobar':
            return 73
        if hg == 'playground/foobar/baz':
            return 99

        raise AssertionError("Your are not allowed to determine id of hostgroup '%s'" % hg)

    def delhostgroup_with_children_search(*req):
        if req[0] == 'hosts':
            return []

        if req[0] == 'hostgroups':
            if req[1] == 'playground/foobar/':
                return [{"title": "playground/foobar/baz",
                         "parent_id": 73}]

        raise AssertionError("Not allowed request")

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=delhostgroup_with_children_resolve)
    @patch.object(ForemanClient, 'search_query',
        side_effect=delhostgroup_with_children_search)
    def test_delhostgroup_fail_with_children(self, *args):
        hg = "playground/foobar"

        self.assertRaises(AiToolsForemanNotAllowedError, self.client.delhostgroup,
            hostgroup=hg)


    def delhostgroup_success_with_children_resolve(hg):
        if hg == 'playground/foobar':
            return 73
        if hg == 'playground/foobar/baz':
            return 99

        raise AssertionError("Your are not allowed to determine id of hostgroup '%s'" % hg)

    def delhostgroup_success_with_children_request(*req):
        if req[0] == 'delete':
            if req[1] == 'https://localhost:1/api/hostgroups/73':
                return generate_response(requests.codes.ok, {"name": "foobar"})
            if req[1] == 'https://localhost:1/api/hostgroups/99':
                return generate_response(requests.codes.ok, {"name": "baz"})

        raise AssertionError("You are not allowed to delete hostgroup '%s'" % hg)

    def delhostgroup_success_with_children_search(*req):
        if req[0] == 'hosts':
            return []

        if req[0] == 'hostgroups':
            if req[1] == 'playground/foobar/':
                return [{"title": "playground/foobar/baz",
                         "parent_id": 73}]
            if req[1] == 'playground/foobar/baz/':
                return []

        raise AssertionError("Not allowed request")

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=delhostgroup_success_with_children_resolve)
    @patch.object(HTTPClient, 'do_request',
        side_effect=delhostgroup_success_with_children_request)
    @patch.object(ForemanClient, 'search_query',
        side_effect=delhostgroup_success_with_children_search)
    def test_delhostgroup_success_with_children(self, *args):
        hg = "playground/foobar"

        self.assertEquals('foobar', self.client.delhostgroup(
            hostgroup=hg, recursive=True))


    def delhostgroup_nested_dryrun_resolve(hg):
        if hg == 'playground':
            return 42
        if hg == 'playground/foobar':
            return 73

        raise AssertionError("You are not allowed to delermine id of hostgroup '%s'" % hg)

    def delhostgroup_nested_dryrun_search(*req):
        if req[0] == 'hosts':
            if req[1] in ['hostgroup_fullname = playground/foobar',
                          'hostgroup_fullname = playground']:
                return []

        if req[0] == 'hostgroups':
            if req[1] == 'playground/':
                return {"title": "playground/foobar", "parent_id": 42}
            if req[1] == 'playground/foobar/':
                return []

        raise AssertionError("You are not allowed to determine %s of hostgroup '%s'" %
                             (req[0], req[1]))

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=delhostgroup_nested_dryrun_resolve)
    @patch.object(ForemanClient, 'search_query',
        side_effect=delhostgroup_nested_dryrun_search)
    @patch.object(HTTPClient, 'do_request')
    def test_delhostgroup_nested_dryrun(self, *args):
        hg = "playground/foobar"
        self.client.dryrun = True
        self.assertEquals(None, self.client.delhostgroup(hostgroup=hg, recursive=True))
        super(ForemanClient, self.client).do_request\
            .assert_not_called()


    def delhostgroup_not_deleted_with_hosts_resolve(hg):
        if hg == 'playground':
            return 42
        if hg == 'playground/foo':
            return 73
        if hg == 'playground/bar':
            return 85
        if hg == 'playground/baz':
            return 89

        raise AssertionError("You are not allowed to delermine id of hostgroup '%s'" % hg)

    def delhostgroup_not_deleted_with_hosts_search(*req):
        if req[0] == 'hosts':
            if 'playground/bar' in req[1]:
                return [{"name": "host1"}]
            return []

        if req[0] == 'hostgroups':
            if req[1] == 'playground/':
                return [{"title": "playground/foo", "parent_id": 42},
                        {"title": "playground/bar", "parent_id": 42},
                        {"title": "playground/baz", "parent_id": 42}]

        raise AssertionError("You are not allowed to determine %s of hostgroup '%s'" %
                             (req[0], req[1]))

    @patch.object(ForemanClient, '_ForemanClient__resolve_hostgroup_id',
        side_effect=delhostgroup_not_deleted_with_hosts_resolve)
    @patch.object(ForemanClient, 'search_query',
        side_effect=delhostgroup_not_deleted_with_hosts_search)
    def test_delhostgroup_not_deleted_with_hosts(self, *args):
        hg = "playground"

        self.assertRaises(AiToolsForemanNotAllowedError, self.client.delhostgroup,
            hostgroup=hg)

    #### RENAMEHOST ####

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK, []),
            generate_response(requests.codes.OK, []),
            generate_response(requests.codes.OK, {
                  "total": 2,
                  "subtotal": 2,
                  "page": 1,
                  "per_page": 50,
                  "search": None,
                  "sort": {
                    "by": None,
                    "order": None
                  },
                  "results": [
                    {
                      "id": 123,
                      "identifier": None,
                      "name": "bar.cern.ch",
                      "primary": True,
                      "provision": True,
                      "type": "interface",
                      "virtual": False
                    },
                    {
                      "id": 124,
                      "identifier": None,
                      "name": "foo-ipmi.cern.ch",
                      "primary": False,
                      "provision": False,
                      "type": "bmc",
                      "provider": "IPMI",
                      "virtual": False
                    }
                  ]
                }),
            generate_response(requests.codes.OK, [])])
    @patch('aitools.foreman.shortify', return_value='foo')
    def test_renamehost_ok(self, *args):
        oldfqdn = "foo.cern.ch"
        newfqdn = "bar.cern.ch"
        expected_payloads = [{"host": {"name": newfqdn}},
            {"host": {"certname": newfqdn}},
            {"interface": {
                    "name": "bar-ipmi.cern.ch",
                    "provider": "IPMI",
                    "type": "bmc"}}]
        expected_calls = [ call('put', full_uri("hosts/%s" %
                urllib.quote(oldfqdn)), ANY, json.dumps(expected_payloads[0])),
            call('put', full_uri("hosts/%s" % urllib.quote(newfqdn)), ANY,
                    json.dumps(expected_payloads[1])),
            call('get', full_uri("hosts/%s/interfaces" % urllib.quote(newfqdn)),
                    ANY, None),
            call('put', full_uri("hosts/%s/interfaces/%d" %
                (urllib.quote(newfqdn), 124)), ANY,
                json.dumps(expected_payloads[2]))]
        self.assertEquals(None, self.client.renamehost(oldfqdn, newfqdn))
        super(ForemanClient, self.client).do_request\
            .assert_has_calls(expected_calls)
        #check that no calls were made other than expected
        self.assertEquals(args[1].call_count, len(expected_calls))

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK, []),
            generate_response(requests.codes.OK, []),
            generate_response(requests.codes.OK, {
                  "total": 2,
                  "subtotal": 2,
                  "page": 1,
                  "per_page": 50,
                  "search": None,
                  "sort": {
                    "by": None,
                    "order": None
                  },
                  "results": [
                    {
                      "id": 123,
                      "identifier": None,
                      "name": "bar.cern.ch",
                      "primary": True,
                      "provision": True,
                      "type": "interface",
                      "virtual": False
                    },
                    {
                      "id": 124,
                      "identifier": None,
                      "name": "special-ipmi.cern.ch",
                      "primary": False,
                      "provision": False,
                      "type": "bmc",
                      "provider": "IPMI",
                      "virtual": False
                    }
                  ]
                }),
            generate_response(requests.codes.OK, [])])
    @patch('aitools.foreman.shortify', return_value='foo')
    def test_renamehost_ok_special_ipmi(self, *args):
        oldfqdn = "foo.cern.ch"
        newfqdn = "bar.cern.ch"
        expected_payloads = [{"host": {"name": newfqdn}},
            {"host": {"certname": newfqdn}}]
        expected_calls = [ call('put', full_uri("hosts/%s" %
                urllib.quote(oldfqdn)), ANY, json.dumps(expected_payloads[0])),
            call('put', full_uri("hosts/%s" % urllib.quote(newfqdn)), ANY,
                    json.dumps(expected_payloads[1])),
            call('get', full_uri("hosts/%s/interfaces" % urllib.quote(newfqdn)),
                    ANY, None)]
        self.assertEquals(None, self.client.renamehost(oldfqdn, newfqdn))
        super(ForemanClient, self.client).do_request\
            .assert_has_calls(expected_calls)
        #check that no calls were made other than expected
        self.assertEquals(args[1].call_count, len(expected_calls))

    @patch.object(HTTPClient, 'do_request', side_effect=
        [
            generate_response(requests.codes.OK, []),
            generate_response(requests.codes.OK, []),
            generate_response(requests.codes.OK, [], meta=True, subtotal=0)])
    @patch('aitools.foreman.shortify', return_value='foo')
    def test_renamehost_ok_no_ipmi(self, *args):
        oldfqdn = "foo.cern.ch"
        newfqdn = "bar.cern.ch"
        expected_payloads = [{"host": {"name": newfqdn}},
            {"host": {"certname": newfqdn}}]
        expected_calls = [ call('put', full_uri("hosts/%s" %
                urllib.quote(oldfqdn)), ANY, json.dumps(expected_payloads[0])),
            call('put', full_uri("hosts/%s" % urllib.quote(newfqdn)), ANY,
                    json.dumps(expected_payloads[1])),
            call('get', full_uri("hosts/%s/interfaces" % urllib.quote(newfqdn)),
                    ANY, None)]
        self.assertEquals(None, self.client.renamehost(oldfqdn, newfqdn))
        super(ForemanClient, self.client).do_request\
            .assert_has_calls(expected_calls)
        #check that no calls were made other than expected
        self.assertEquals(args[1].call_count, len(expected_calls))

    @patch.object(HTTPClient, 'do_request', return_value=
        generate_response(requests.codes.not_found, [], meta=True))
    def test_renamehost_host_not_found(self, *args):
        oldfqdn = "foo.cern.ch"
        newfqdn = "bar.cern.ch"
        expected_payloads = [{"host": {"name": newfqdn}}]
        expected_calls = [ call('put', full_uri("hosts/%s" %
                urllib.quote(oldfqdn)), ANY, json.dumps(expected_payloads[0]))]
        self.assertRaises(AiToolsForemanNotFoundError,
            self.client.renamehost, oldfqdn, newfqdn)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls(expected_calls)
        #check that no calls were made other than expected
        self.assertEquals(args[0].call_count, len(expected_calls))

    @patch.object(HTTPClient, 'do_request', return_value=
        generate_response(requests.codes.unprocessable_entity, [], meta=True))
    def test_renamehost_host_unprocessable(self, *args):
        oldfqdn = "foo.cern.ch"
        newfqdn = "bar.cern.ch"
        expected_payloads = [{"host": {"name": newfqdn}}]
        expected_calls = [ call('put', full_uri("hosts/%s" %
                urllib.quote(oldfqdn)), ANY, json.dumps(expected_payloads[0]))]
        self.assertRaises(AiToolsForemanError,
            self.client.renamehost, oldfqdn, newfqdn)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls(expected_calls)
        self.assertEquals(args[0].call_count, len(expected_calls))


    @patch.object(HTTPClient, 'do_request', return_value=
        generate_response(requests.codes.server_error, [], meta=True))
    def test_renamehost_server_error(self, *args):
        oldfqdn = "foo.cern.ch"
        newfqdn = "bar.cern.ch"
        expected_payloads = [{"host": {"name": newfqdn}}]
        expected_calls = [ call('put', full_uri("hosts/%s" %
                urllib.quote(oldfqdn)), ANY, json.dumps(expected_payloads[0]))]
        self.assertRaises(AiToolsForemanError,
            self.client.renamehost, oldfqdn, newfqdn)
        super(ForemanClient, self.client).do_request\
            .assert_has_calls(expected_calls)
        self.assertEquals(args[0].call_count, len(expected_calls))

    #### CREATE_ROLE ####

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.created, {
            "builtin": 0,
            "name": "foo",
            "id": 123,
            "filters": []}))
    def test_create_role_ok(self, *args):
        self.assertEquals(123, self.client.create_role("foo"))
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("roles"), ANY, json.dumps(
                {"role":{"name": "foo"}}))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.server_error, []))
    def test_create_role_not_ok(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.create_role, "foo")
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("roles"), ANY, json.dumps(
                {"role":{"name": "foo"}}))


    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.created, {
            "builtin": 0,
            "name": "foo",
            "filters": []}))
    def test_create_role_keyerror(self, *args):
        self.assertRaises(AiToolsForemanError,
            self.client.create_role, "foo")
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("roles"), ANY, json.dumps(
                {"role":{"name": "foo"}}))

    #### GET_PERMISSIONS_BY_MODEL ####
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.ok,
        {"total": 2,
          "subtotal": 2,
          "page": 1,
          "per_page": 20,
          "search": None,
          "sort": {
            "by": None,
            "order": None
          },
          "results": [
            {
              "name": "perm1",
              "id": 124,
              "resource_type": "resource"
            },
            {
              "name": "perm2",
              "id": 123,
              "resource_type": "resource"
            }]}))
    def test_getpermissionssbymodel_ok(self, *args):
        self.assertEquals([123,124], self.client.get_permissions_by_model("resource"))
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get', full_uri("permissions"), ANY, json.dumps(
                {"resource_type":"resource"}))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.server_error, []))
    def test_getpermissionssbymodel_not_ok(self, *args):
        self.assertRaises(AiToolsForemanError, self.client.get_permissions_by_model, "resource")
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get', full_uri("permissions"), ANY, json.dumps(
                {"resource_type":"resource"}))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.ok,
        {"total": 2,
          "subtotal": 2,
          "page": 1,
          "per_page": 20,
          "search": None,
          "sort": {
            "by": None,
            "order": None
          },
          "results": [
            {
              "name": "perm1",
              "resource_type": "resource"
            },
            {
              "name": "perm2",
              "resource_type": "resource"
            }]}))
    def test_getpermissionssbymodel_keyerror(self, *args):
        self.assertRaises(AiToolsForemanError,
            self.client.get_permissions_by_model, "resource")
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('get', full_uri("permissions"), ANY, json.dumps(
                {"resource_type":"resource"}))

    #### CREATE_FILTER ####
    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.created,
        {
          "search": "hostgroup_title ~ foo",
          "resource_type": "Architecture",
          "unlimited?": True,
          "created_at": "2016-03-10 15:51:57 UTC",
          "updated_at": "2016-03-10 15:51:57 UTC",
          "id": 123,
          "role": {
            "name": "Manager",
            "id": 1
          },
          "permissions": [],
          "organizations": [],
          "locations": []
        }))
    def test_create_filter_ok_search(self, *args):
        expected_load = {"filter": {"role_id": "1",
            "search":"hostgroup_title ~ foo"}}
        self.assertEquals(123, self.client.create_filter(1,
            search="hostgroup_title ~ foo"))
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("filters"), ANY,
            json.dumps(expected_load))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.created,
        {
          "search": None,
          "resource_type": "Architecture",
          "unlimited?": True,
          "created_at": "2016-03-10 15:51:57 UTC",
          "updated_at": "2016-03-10 15:51:57 UTC",
          "id": 123,
          "role": {
            "name": "Manager",
            "id": 1
          },
          "permissions": [
            {
              "name": "view_architectures",
              "id": 2,
              "resource_type": "Architecture"
            }
          ],
          "organizations": [],
          "locations": []
        }))
    def test_create_filter_ok_permissions(self, *args):
        expected_load = {"filter": { "role_id": "1","permission_ids": [2]}}
        self.assertEquals(123, self.client.create_filter(1,permission_ids=[2]))
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("filters"), ANY,
            json.dumps(expected_load))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.created,
        {
          "search": "hostgroup_title ~ foo",
          "resource_type": "Architecture",
          "unlimited?": True,
          "created_at": "2016-03-10 15:51:57 UTC",
          "updated_at": "2016-03-10 15:51:57 UTC",
          "id": 123,
          "role": {
            "name": "Manager",
            "id": 1
          },
          "permissions": [
            {
              "name": "view_architectures",
              "id": 2,
              "resource_type": "Architecture"
            }
          ],
          "organizations": [],
          "locations": []
        }))
    def test_create_filter_ok_full(self, *args):
        expected_load = {"filter": {"role_id": "1", "permission_ids": [2],
            "search":"hostgroup_title ~ foo"}}
        self.assertEquals(123, self.client.create_filter(1,
            "hostgroup_title ~ foo", [2]))
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("filters"), ANY,
            json.dumps(expected_load))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.created,
        {
          "search": None,
          "resource_type": "Architecture",
          "unlimited?": True,
          "created_at": "2016-03-10 15:51:57 UTC",
          "updated_at": "2016-03-10 15:51:57 UTC",
          "id": 123,
          "role": {
            "name": "Manager",
            "id": 1
          },
          "permissions": [],
          "organizations": [],
          "locations": []
        }))
    def test_create_filter_ok(self, *args):
        expected_load = {"filter": { "role_id": "1"}}
        self.assertEquals(123, self.client.create_filter(1))
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("filters"), ANY,
            json.dumps(expected_load))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.server_error, []))
    def test_create_filter_not_ok(self, *args):
        expected_load = {"filter": { "role_id": "1"}}
        self.assertRaises(AiToolsForemanError, self.client.create_filter, 1)
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("filters"), ANY,
            json.dumps(expected_load))

    @patch.object(HTTPClient, 'do_request',
        return_value=generate_response(requests.codes.created,
        {
          "search": None,
          "resource_type": "Architecture",
          "unlimited?": True,
          "created_at": "2016-03-10 15:51:57 UTC",
          "updated_at": "2016-03-10 15:51:57 UTC",
          "role": {
            "name": "Manager",
            "id": 1
          },
          "permissions": [],
          "organizations": [],
          "locations": []
        }))
    def test_create_filter_keyerror(self, *args):
        expected_load = {"filter": { "role_id": "1"}}
        self.assertRaises(AiToolsForemanError,
            self.client.create_filter, 1)
        super(ForemanClient, self.client).do_request\
            .assert_called_once_with('post', full_uri("filters"), ANY,
            json.dumps(expected_load))

    def test_create_filter_typeerror(self, *args):
        self.assertRaises(TypeError, self.client.create_filter, 1,
            permission_ids="1,2")
