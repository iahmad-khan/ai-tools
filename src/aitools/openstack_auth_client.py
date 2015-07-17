#!/usr/bin/env python
#  Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch>

import logging
import requests
from keystoneclient.v3 import client as keystoneclient
from openstackclient.common import clientmanager
from keystoneclient import exceptions
from keystoneclient.openstack.common.apiclient import exceptions as api_exceptions
from aitools.errors import AiToolsOpenstackAuthError

class OpenstackAuthClient():
    def __init__(self, auth_options):
        """
        Wrapper class for openstackclient.common.ClientManager. It does the
        authentication against Nova, Cinder and Glance.
        """
        try:
            self.client = clientmanager.ClientManager(auth_options=auth_options,
                api_version={'identity': auth_options.os_identity_api_version},
                verify=True,
                pw_func=None)

        except exceptions.SSLError:
            raise AiToolsOpenstackAuthError("x509 client certificate error")
        except (api_exceptions.Unauthorized, api_exceptions.Forbidden,
            api_exceptions.NotFound):
            raise AiToolsOpenstackAuthError("- Are you using the wrong tenant?\n"
                " - Is your Kerberos ticket expired?")

    def get_tenant_uuid(self, proj_name, username):
        try:
            keystone = keystoneclient.Client(session=self.client.session)
            projects_id = [tenant.id for tenant in
                keystone.projects.list(user=username) \
                if tenant.name == proj_name]
            if not projects_id:
                raise AiToolsOpenstackAuthError("There is no Openstack project with name:"
                    " '%s'" % proj_name)
            if len(projects_id) > 1:
                raise AiToolsOpenstackAuthError("There are more than one Openstack project with name:"
                    " '%s'" % proj_name)
            return projects_id[0]
        except requests.exceptions.Timeout, error:
            raise AiToolsOpenstackAuthError(error)
        except exceptions.ClientException, error:
            raise AiToolsOpenstackAuthError(error)

    @property
    def session(self):
        logging.debug('Getting session from OpenStack ClientManager')
        return self.client.session
