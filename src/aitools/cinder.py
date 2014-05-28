#!/usr/bin/env python
#  Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch>

import logging
import requests
import cinderclient.exceptions
from cinderclient.v1 import client

from aitools.errors import AiToolsCinderError

class CinderClient():
    def __init__(self, username, password,
            tenant_id, auth_url, cacert, dryrun=False):
        """
        Cinder client for interacting with the Openstack Cinder service. .

        :param username: override the environment variable configured username
        :param password: override the environment variable configured password
        :param tenant_id: override the environment variable configured Tenant ID
        :param auth_url: override the environment variable configured Keystone URL
        :param cacert: override the environment variable configured CA certificate bundle
        :param dryrun: create a dummy client
        """
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.tenant_id = tenant_id
        self.cacert = cacert
        self.dryrun = dryrun

    def get(self, volume_id):
        """
        Get the volume with id = volume_id.

        """
        tenant = self.__init_client()
        try:
            logging.info("Getting volume '%s' from Cinder" % volume_id)
            return tenant.volumes.get(volume_id=volume_id)
        except cinderclient.exceptions.NotFound:
            # Cinder volume doesn't exist
            raise AiToolsCinderError("Volume '%s' doesn't exist" % volume_id)
        except requests.exceptions.Timeout, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ClientException, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ConnectionError, error:
            raise AiToolsCinderError(error)

    def is_ready_to_boot(self, volume):
        return volume.status == 'available' and volume.bootable == 'true'

    def __init_client(self):
        try:
            return client.Client(self.username, self.password,
                    tenant_id=self.tenant_id,
                    auth_url=self.auth_url,
                    cacert=self.cacert)
        except cinderclient.exceptions.ClientException, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ConnectionError, error:
            raise AiToolsCinderError(error)

