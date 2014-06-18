#!/usr/bin/env python
#  Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch>

import time
import logging
import requests
import cinderclient.exceptions
from cinderclient.v1 import client

from aitools.errors import AiToolsCinderError

class CinderClient():

    DEFAULT_TIMEOUT_PER_GB = 20

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

    def create(self, size, display_name=None, display_description=None,
               volume_type=None, imageRef=None):
        """
        Execute the Cinder create api call to create a Volume.

        :param size: the size used to create the volume
        :param display_name: the name of the volume
        :param display_description: the description of the volume
        :param volume_type: the type of the volume
        :param imageRef: the image to be turned into a volume
        :raise AiToolsCinderError: in case the API call fails
        """
        vol_name = display_name or ''
        logging.info("Creating volume %s ..." % vol_name)
        tenant = self.__init_client()
        try:
            if not self.dryrun:
                return tenant.volumes.create(size=size,
                    display_name=display_name,
                    display_description=display_description,
                    volume_type=volume_type,
                    imageRef=imageRef)
                logging.info("Request to create volume %s sent" % vol_name)
            else:
                logging.info("Volume %s not created because dryrun is enabled" % vol_name)
        except requests.exceptions.Timeout, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ClientException, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ConnectionError, error:
            raise AiToolsCinderError(error)

    def get(self, volume_id):
        """
        Get the volume with id = volume_id.

        """
        tenant = self.__init_client()
        try:
            volume = tenant.volumes.get(volume_id=volume_id)
            logging.info("Getting volume '{0}' from Cinder. It has status: "
                "'{1}' and is {2}bootable".format(volume.id, volume.status,
                    ('NOT ' if volume.bootable == 'false' else '')))
            return volume
        except cinderclient.exceptions.NotFound:
            # Cinder volume doesn't exist
            raise AiToolsCinderError("Volume '%s' doesn't exist" % volume_id)
        except requests.exceptions.Timeout, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ClientException, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ConnectionError, error:
            raise AiToolsCinderError(error)

    def is_ready_to_boot(self, volume_id, wait_until_ready=False, waittime=10):
        """
        Check if the volume is ready to boot i.e. its status is 'available' and
        the bootable flag is 'True'. If it's ready, the volume is returned, if
        not, 'None' instead.

        :param volume_id: volume to be checked
        :param wait_until_ready: if True it will wait until the status is no
            longer 'creating' or 'downloading'. This is useful when the volume
            has been recently created and we are waiting to boot from it
        :param waittime: time to wait between checking if the volume is ready
        :raise AiToolsCinderError: in case the volume doesn't get created
            before the timeout
        """
        if volume_id:
            volume = self.get(volume_id)
            if wait_until_ready:
                timeout = self.DEFAULT_TIMEOUT_PER_GB * volume.size
                time_init = time.time()
                time_elapsed = str(time.time() - time_init).split('.')[0]
                while volume.status == 'creating' or volume.status == 'downloading':
                    if int(time_elapsed) > timeout:
                        raise AiToolsCinderError("Volume '{0}' took more than {1} "
                            "seconds to be created. Time elapsed: {2} seconds"
                            .format(volume.id, timeout, time_elapsed))
                    logging.info("Volume '{0}' is being created. This operation can"
                        " take several minutes, please wait.".format(volume.id))
                    time.sleep(waittime)
                    time_elapsed = str(time.time() - time_init).split('.')[0]
                    logging.info("Time elapsed: {0} seconds".format(time_elapsed))
                    volume = self.get(volume.id)
            if volume.status == 'available' and volume.bootable == 'true':
                return volume
        raise AiToolsCinderError("Error booting from volume. Volume must be "
            "'available' and bootable")

    def __init_client(self):
        try:
            return client.Client(self.username, self.password,
                    tenant_id=self.tenant_id,
                    auth_url=self.auth_url,
                    cacert=self.cacert)
        except requests.exceptions.Timeout, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ClientException, error:
            raise AiToolsCinderError(error)
        except cinderclient.exceptions.ConnectionError, error:
            raise AiToolsCinderError(error)

