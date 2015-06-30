__author__ = 'Alberto Rodriguez Peon'

import unittest
from requests import Timeout
from mock import Mock, patch
from uuid import uuid4
from openstackclient.common import clientmanager
from keystoneclient.v2_0 import client as keystone
from keystoneclient import exceptions

from aitools.errors import AiToolsOpenstackAuthError
from aitools.openstack_auth_client import OpenstackAuthClient

class TestOpenstackAuthClient(unittest.TestCase):

    def setUp(self):
        clientmanager.ClientManager = Mock(token='')
        self.auth_client = OpenstackAuthClient(auth_url='fake url', **{})
        self.expected_uuid = str(uuid4())

    def test_valid_tenant_name(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 1'
        keystone.Client = Mock()
        keystone.Client.return_value.tenants.list.return_value = tenants

        self.assertTrue(self.auth_client.get_tenant_uuid('Project 1') == self.expected_uuid)

    def test_unknown_tenant_name(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock()
        keystone.Client.return_value.tenants.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError, self.auth_client.get_tenant_uuid, 'Project 1')

    def test_timeout(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=Timeout)
        keystone.Client.return_value.tenants.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError, self.auth_client.get_tenant_uuid, 'Project 1')

    def test_clientexception(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=exceptions.ClientException)
        keystone.Client.return_value.tenants.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError, self.auth_client.get_tenant_uuid, 'Project 1')

    def test_connectionrefused(self):
        tenants = [Mock(id=self.expected_uuid)]
        tenants[0].name = 'Project 2'
        keystone.Client = Mock(side_effect=exceptions.ConnectionRefused)
        keystone.Client.return_value.tenants.list.return_value = tenants

        self.assertRaises(AiToolsOpenstackAuthError, self.auth_client.get_tenant_uuid, 'Project 1')


