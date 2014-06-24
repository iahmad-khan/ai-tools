#!/usr/bin/env python
#  Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch>

import time
import logging
import requests
import cinderclient.exceptions
from cinderclient.v1 import client

from aitools.errors import AiToolsCinderError

class CinderClient():

    DEFAULT_TIMEOUT= 360

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
        try:
            size_in_GB = int(size)
        except ValueError:
            # size is in the format 'XGB' or 'XTB'
            size_in_GB, unit = int(size[:-2]), size[-2:]
            if unit == 'TB':
                size_in_GB *= 1024

        logging.info("Creating volume %s ..." % vol_name)
        tenant = self.__init_client()
        try:
            if not self.dryrun:
                return tenant.volumes.create(size=size_in_GB,
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

    def is_ready_to_boot(self, volume_id, wait_until_ready=False, timeout=DEFAULT_TIMEOUT,
        wait_time=60):
        """
        Check if the volume is ready to boot i.e. its status is 'available' and
        the bootable flag is 'True'. If it's ready, the volume is returned, if
        not, 'None' instead.

        :param volume_id: volume to be checked
        :param wait_until_ready: if True it will wait until the status is no
            longer 'creating' or 'downloading'. This is useful when the volume
            has been recently created and we are waiting to boot from it
        :param timeout: maximum time spent waiting for a volume
        :param wait_time: time to wait between checking if the volume is ready
        :raise AiToolsCinderError: in case the volume doesn't get created
            before the timeout
        """
        if volume_id:
            volume = self.get(volume_id)
            if wait_until_ready:
                time_init = time.time()
                while volume.status == 'creating' or volume.status == 'downloading':
                    time_elapsed = int(time.time() - time_init)
                    if time_elapsed > timeout:
                        raise AiToolsCinderError("Volume '{0}' took more than {1} "
                            "seconds to be created. Time elapsed: {2} seconds"
                            .format(volume.id, timeout, time_elapsed))
                    logging.info("Volume not created yet. Checking again in %s seconds" % wait_time)
                    time.sleep(wait_time)
                    logging.debug("Time elapsed: {0} seconds".format(time_elapsed))
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

