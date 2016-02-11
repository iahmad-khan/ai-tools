#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import logging
import requests
import dateutil.parser

from glanceclient.exc import ClientException
from glanceclient.v2 import client

from aitools.config import GlanceConfig
from aitools.errors import AiToolsGlanceError

class GlanceClient():
    def __init__(self, auth_client, timeout=0, dryrun=False):
        """
        Glance client for interacting with the Openstack Image service. Autoconfigures via the AiConfig
        object and the standard **_OS** environment variables.

        :param auth_client: OpenstackAuthClient that does the authentication
        :param timeout: override the auto-configured Glance timeout
        :param dryrun: create a dummy client
        """
        glanceconfig = GlanceConfig()
        self.glance = None
        self.auth_client = auth_client
        self.timeout = int(timeout or glanceconfig.glance_timeout)
        self.dryrun = dryrun

    def get_latest_image(self, os_distro, os_distro_major, os_edition='Base',
            architecture='x86_64'):
        glance = self.__init_client()
        try:
            filtered_images = [image for image in glance.images.list() if
                'release_date' in image and
                image.get('os_distro_minor') is not None and
                image.get('os_distro') == os_distro and
                image.get('os_distro_major') == str(os_distro_major) and
                image.get('os_edition') == os_edition and
                image.get('architecture') == architecture and
                image.get('visibility') == 'public']

            if not filtered_images:
                raise AiToolsGlanceError("No available '%s%s' image for '%s' "
                    "architecture" % (os_distro, os_distro_major, architecture))

            latest = max(filtered_images,
                key=lambda image: (int(image['os_distro_minor']),
                                   dateutil.parser.parse(image['release_date'])))

            logging.info("Using '%s' as the latest '%s%s' image available"
                "" % (latest.get('name') or latest['id'], os_distro, os_distro_major))
            return latest['id']

        except (requests.exceptions.Timeout, ClientException) as error:
            raise AiToolsGlanceError(error)

    def __init_client(self):
        if self.glance is None:
            try:
                endpoint = self.auth_client.client.get_endpoint_for_service_type('image')
                token = self.auth_client.client.auth.get_token(self.auth_client.session)
                self.glance = client.Client(endpoint=endpoint, token=token)
            except Exception, error:
                raise AiToolsGlanceError(error)
        return self.glance
