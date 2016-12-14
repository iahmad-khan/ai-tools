#!/usr/bin/env python
#  Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch>

import logging
import requests
import re
from keystoneauth1 import session as keystone_session
from keystoneauth1 import exceptions as ka_exceptions
from keystoneclient.v3 import client as keystoneclient
from openstackclient.api import auth
from openstackclient.common import clientmanager
from os_client_config import config as cloud_config
from keystoneclient import exceptions as ks_exceptions
from aitools.errors import AiToolsOpenstackAuthError
from aitools.errors import AiToolsOpenstackAuthBadEnvError

class OpenstackAuthClient():
    def __init__(self, auth_options):
        """
        Wrapper class for openstackclient.common.ClientManager. It does the
        authentication against Nova, Cinder and Glance.
        """
        try:

            # This should prevent the program from continuing if an old
            # openrc is sourced and there is nothing set globally.
            if not hasattr(auth_options, 'os_identity_api_version') or \
                auth_options.os_identity_api_version != "3":
                raise AiToolsOpenstackAuthBadEnvError('os_identity_api_version')

            # In case an old openrc is sourced, mixing up global configuration
            # (v3) and local (v2).
            if hasattr(auth_options, 'os_auth_url') and \
                re.match(r'.*v2(\.0)?/?$', auth_options.os_auth_url):
                raise AiToolsOpenstackAuthBadEnvError('os_auth_url')

            self.session, auth_plugin = self.__make_session(auth_options)

            self.__validate_session(auth_plugin)

        except ks_exceptions.SSLError:
            raise AiToolsOpenstackAuthError("x509 client certificate error")
        except (ka_exceptions.http.Unauthorized, ka_exceptions.NotFound):
            raise AiToolsOpenstackAuthError("Wrong tenant? Kerberos ticket expired?")

    def __validate_session(self, auth_plugin):
        """ Requests a token from Keystone to make sure that the
        credetials are okay and the calling user has access to the tenant.
        This way we can fail early and inform the calling user quickly"""
        auth_plugin.get_auth_ref(self.session)

    def __make_session(self, opts, **kwargs):
        """Create our base session using simple auth from ksc plugins
        The arguments required in opts varies depending on the auth plugin
        that is used.  This example assumes Identity v2 will be used
        and selects token auth if both os_url and os_token have been
        provided, otherwise it uses password.
        :param opts:
            A parser options containing the authentication
            options to be used
        :param dict kwargs:
            Additional options passed directly to Session constructor
        """
        cc = cloud_config.OpenStackConfig()
        cloud = cc.get_one_cloud(argparse=opts)

        # init OS plugin list
        auth.get_plugin_list()

        auth_plugin_name = auth.select_auth_plugin(cloud)
        (auth_plugin, auth_params) = auth.build_auth_params(
            auth_plugin_name,
            cloud,
        )


        auth_plugin = auth_plugin.load_from_options(**auth_params)
        session = keystone_session.Session(
            auth=auth_plugin,
            **kwargs
        )

        return (session, auth_plugin)

    def get_tenant_uuid(self, proj_name, username):
        try:
            keystone = keystoneclient.Client(session=self.session)
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
        except ks_exceptions.ClientException, error:
            raise AiToolsOpenstackAuthError(error)
