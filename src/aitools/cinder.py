#!/usr/bin/env python
#  Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch>

import time
import logging
import requests
import cinderclient.exceptions
from cinderclient.v1 import client
from aitools.errors import AiToolsCinderError

class CinderClient():

    DEFAULT_TIMEOUT = 360
    def __init__(self, auth_client, dryrun=False):
        """
        Cinder client for interacting with the Openstack Cinder service.

        :param auth_client: OpenstackAuthClient that does the authentication
        :param dryrun: create a dummy client
        """
        self.cinder = None
        self.auth_client = auth_client
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
        vol_name = "'" + display_name + "' " if display_name else ''
        try:
            size_in_GB = int(size)
        except ValueError:
            # size is in the format 'XGB' or 'XTB'
            size_in_GB, unit = int(size[:-2]), size[-2:]
            if unit == 'TB':
                size_in_GB *= 1024

        logging.info("Creating volume %s..." % vol_name)
        tenant = self.__init_client()
        try:
            if not self.dryrun:
                volume = tenant.volumes.create(size=size_in_GB,
                    display_name=display_name,
                    display_description=display_description,
                    volume_type=volume_type,
                    imageRef=imageRef)
                logging.info("Request to create volume %ssent" % vol_name)
                return volume
            else:
                logging.info("Volume %snot created because dryrun is enabled" % vol_name)
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

    def is_ready(self, volume_id, needs_to_be_bootable=False,
        timeout=DEFAULT_TIMEOUT, wait_time=60):
        """
        Check if the volume is ready i.e. its status is 'available'.
        If it's ready, the volume is returned, if not, an exception is
        raised.

        :param volume_id: volume to be checked
        :param needs_to_be_bootable: if True it will check that the volume's
            bootable flag is True
        :param timeout: maximum time spent waiting for a volume
        :param wait_time: time to wait between checking if the volume is ready
        :raise AiToolsCinderError: in case the volume doesn't get created
            before the timeout
        """
        if volume_id:
            volume = self.get(volume_id)
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
            if volume.status == 'available':
                if not needs_to_be_bootable or volume.bootable == 'true':
                    return volume
        raise AiToolsCinderError("Error booting from volume. Volume must be "
            "'available'{0}".format(' and bootable' if needs_to_be_bootable else ''))

    def __init_client(self):
        if self.cinder is None:
            try:
                self.cinder = client.Client(username='', api_key='', project_id='', auth_url='')
                self.cinder.client.auth_token = self.auth_client.token
                self.cinder.client.management_url = self.auth_client.cinder_endpoint
            except requests.exceptions.Timeout, error:
                raise AiToolsCinderError(error)
            except cinderclient.exceptions.ClientException, error:
                raise AiToolsCinderError(error)
            except cinderclient.exceptions.ConnectionError, error:
                raise AiToolsCinderError(error)
        return self.cinder

