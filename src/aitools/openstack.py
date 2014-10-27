#!/usr/bin/env python
#  Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch>

import logging
from openstackclient.common import clientmanager
from keystoneclient import exceptions
from keystoneclient.openstack.common.apiclient import exceptions as api_exceptions
from aitools.errors import AiToolsOpenstackError

class OpenstackClient():
    def __init__(self, auth_url, project_name=None, project_id=None,
        username=None, password=None, identity_api_version='2.0',
        domain_id=None, domain_name=None, user_domain_id=None,
        user_domain_name=None, project_domain_id=None, project_domain_name=None,
        clientcert=None, clientkey=None, cacert=None):
        """
        Wrapper class for openstackclient.common.ClientManager. It does the
        authentication against Nova, Cinder and Glance.
        """
        try:
            self.client = clientmanager.ClientManager(auth_url=auth_url,
                project_name=project_name,
                project_id=project_id,
                username=username,
                password=password,
                region_name='',
                api_version={'identity': identity_api_version},
                verify=True,
                trust_id='',
                domain_id=domain_id,
                domain_name=domain_name,
                user_domain_id=user_domain_id,
                user_domain_name=user_domain_name,
                project_domain_id=project_domain_id,
                project_domain_name=project_domain_name,
                timing=False,
                client_cert=(clientcert, clientkey) if clientcert and clientkey else None)

        except exceptions.SSLError:
            raise AiToolsOpenstackError("x509 client certificate error")
        except api_exceptions.Unauthorized:
            raise AiToolsOpenstackError("User not authorized to perform "
                "this operation (Wrong tenant?)")

    @property
    def token(self):
        logging.debug('Getting token from OpenStack ClientManager')
        return self.client._token

    @property
    def nova_endpoint(self):
        logging.debug('Getting nova_endpoint from OpenStack ClientManager')
        return self.client.get_endpoint_for_service_type('compute')

    @property
    def cinder_endpoint(self):
        logging.debug('Getting cinder_endpoint from OpenStack ClientManager')
        return self.client.get_endpoint_for_service_type('volume')

    @property
    def glance_endpoint(self):
        logging.debug('Getting glance_endpoint from OpenStack ClientManager')
        return self.client.get_endpoint_for_service_type('image')
