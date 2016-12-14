__author__ = 'Alberto Rodriguez Peon'

import unittest
from requests import Timeout
from mock import Mock, patch
from uuid import uuid4
from openstackclient.common import clientmanager
from keystoneclient.v3 import client as keystone
from keystoneclient import exceptions
from keystoneauth1 import exceptions as ka_exceptions

from aitools.errors import AiToolsOpenstackAuthError
from aitools.errors import AiToolsOpenstackAuthBadEnvError
from aitools.common import OpenstackEnvironmentVariables
from aitools.openstack_auth_client import OpenstackAuthClient

class TestOpenstackAuthClient(unittest.TestCase):

    def setUp(self):
        clientmanager.ClientManager = Mock(session='')
        self.osvars = OpenstackEnvironmentVariables(**
            {'os_auth_url': 'http://example.org/v3',
             'os_identity_api_version': '3'})
        self.expected_uuid = str(uuid4())

    ## init

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_invalid_identity_api_version(self, mock_oac):
        osvars = OpenstackEnvironmentVariables(**
            {'os_auth_url': 'http://example.org/v2',
             'os_identity_api_version': '2'})
        self.assertRaises(AiToolsOpenstackAuthBadEnvError,
            OpenstackAuthClient, osvars)

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_invalid_auth_url(self, mock_oac):
        osvars = OpenstackEnvironmentVariables(**
            {'os_auth_url': 'http://example.org/v2.0',
             'os_identity_api_version': '3'})
        self.assertRaises(AiToolsOpenstackAuthBadEnvError,
            OpenstackAuthClient, osvars)

    ## __validate_session

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_make_session_bad_tenant_authorised(self, mock_oac):
        mock_oac.side_effect = ka_exceptions.http.NotFound
        self.assertRaises(AiToolsOpenstackAuthError,
            OpenstackAuthClient, self.osvars)

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_make_session_bad_tenant_not_found(self, mock_oac):
        mock_oac.side_effect = ka_exceptions.http.Unauthorized
        self.assertRaises(AiToolsOpenstackAuthError,
            OpenstackAuthClient, self.osvars)
    ## get_tenant_uuid

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_valid_tenant_name(self, mock_oac):
        auth_client = OpenstackAuthClient(self.osvars)
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 1'
        keystone.Client = Mock()
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertEquals(auth_client.get_tenant_uuid('Project 1',
            'foouser'), self.expected_uuid)

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_unknown_tenant_name(self, mock_oac):
        auth_client = OpenstackAuthClient(self.osvars)
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock()
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError,
            auth_client.get_tenant_uuid, 'Project 1', 'foouser')

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_timeout(self, mock_oac):
        auth_client = OpenstackAuthClient(self.osvars)
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=Timeout)
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError,
            auth_client.get_tenant_uuid, 'Project 1', 'foouser')

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_clientexception(self, mock_oac):
        auth_client = OpenstackAuthClient(self.osvars)
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=exceptions.ClientException)
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError,
            auth_client.get_tenant_uuid, 'Project 1', 'foouser')

    @patch.object(OpenstackAuthClient, '_OpenstackAuthClient__validate_session')
    def test_connectionrefused(self, mock_oac):
        auth_client = OpenstackAuthClient(self.osvars)
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=exceptions.ConnectionRefused)
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError,
            auth_client.get_tenant_uuid, 'Project 1', 'foouser')
