__author__ = 'Alberto Rodriguez Peon'

import unittest
from requests import Timeout
from mock import Mock, patch
from uuid import uuid4
from openstackclient.common import clientmanager
from keystoneclient.v3 import client as keystone
from keystoneclient import exceptions

from aitools.errors import AiToolsOpenstackAuthError
from aitools.errors import AiToolsOpenstackAuthBadEnvError
from aitools.common import OpenstackEnvironmentVariables
from aitools.openstack_auth_client import OpenstackAuthClient

class TestOpenstackAuthClient(unittest.TestCase):

    def setUp(self):
        clientmanager.ClientManager = Mock(session='')
        osvars = OpenstackEnvironmentVariables(**
            {'os_auth_url': 'http://example.org/v3',
             'os_identity_api_version': '3'})
        self.auth_client = OpenstackAuthClient(osvars)
        self.expected_uuid = str(uuid4())

    def test_valid_tenant_name(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 1'
        keystone.Client = Mock()
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertEquals(self.auth_client.get_tenant_uuid('Project 1',
            'foouser'), self.expected_uuid)

    def test_unknown_tenant_name(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock()
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError,
            self.auth_client.get_tenant_uuid, 'Project 1', 'foouser')

    def test_timeout(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=Timeout)
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError,
            self.auth_client.get_tenant_uuid, 'Project 1', 'foouser')

    def test_clientexception(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=exceptions.ClientException)
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError,
            self.auth_client.get_tenant_uuid, 'Project 1', 'foouser')

    def test_connectionrefused(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=exceptions.ConnectionRefused)
        keystone.Client.return_value.projects.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError,
            self.auth_client.get_tenant_uuid, 'Project 1', 'foouser')
