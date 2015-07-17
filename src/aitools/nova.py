#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import re
import logging
import novaclient.exceptions
import requests
from novaclient.v1_1 import client
from aitools.config import NovaConfig
from aitools.common import is_valid_UUID

from aitools.errors import AiToolsNovaError


class NovaClient():
    def __init__(self, auth_client, timeout=0, dryrun=False):
        """
        Nova client for interacting with the Openstack Nova service. Autoconfigures via the AiConfig
        object and the standard **_OS** environment variables.

        :param auth_client: OpenstackAuthClient that does the authentication
        :param timeout: override the auto-configured Nova timeout
        :param dryrun: create a dummy client
        """
        novaconfig = NovaConfig()
        self.nova = None
        self.auth_client = auth_client
        self.timeout = int(timeout or novaconfig.nova_timeout)
        self.dryrun = dryrun

    def boot(self, fqdn, flavor, image, userdata, meta,
            key_name=None, availability_zone=None, block_device_mapping=None):
        """
        Execute the Nova boot api call to create and start a VM.

        :param fqdn: the hostname to create
        :param flavor: the flavor used to create the node
        :param image: the image name used to create the node
        :param userdata: the userdata to append
        :param meta: the metadata to append
        :param key_name: the named SSH key to use
        :param availability_zone: the availability zone to create the node in
        :raise AiToolsNovaError: in case the API call fails
        """
        vmname = self.__vmname_from_fqdn(fqdn)
        logging.info("Creating virtual machine '%s'..." % vmname)
        tenant = self.__init_client()
        try:
            flavor_id = self.__resolve_id(tenant.flavors.list(), flavor)
            logging.debug("Flavor '%s' has id '%s'" % (flavor, flavor_id))
            image_id = self.__resolve_id(tenant.images.list(), image) if image else None
            logging.debug("Image '%s' has id '%s'" % (image, image_id))
            if not self.dryrun:
                tenant.servers.create(name=vmname,
                    image=image_id,
                    flavor=flavor_id,
                    userdata=userdata,
                    meta=meta,
                    key_name=key_name,
                    availability_zone=availability_zone,
                    block_device_mapping=block_device_mapping)
                logging.info("Request to create VM '%s' sent" % vmname)
            else:
                logging.info("VM '%s' not created because dryrun is enabled" % vmname)
        except requests.exceptions.Timeout, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ClientException, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ConnectionRefused, error:
            raise AiToolsNovaError(error)

    def rebuild(self, fqdn, image=None):
        """
        Execute the Nova boot api call to rebuild a VM.

        :param fqdn: the FQDN of the VM to be rebuilt
        :param image: the image name to base the rebuilt on.
            If None, the current one will be used.
        :raise AiToolsNovaError: in case the API call fails
        """
        vmname = self.__vmname_from_fqdn(fqdn)
        logging.info("Rebuilding virtual machine '%s'..." % vmname)
        tenant = self.__init_client()
        try:
            server_id = self.__resolve_id(tenant.servers.list(), vmname)
            logging.debug("Server '%s' has id '%s'" % (vmname, server_id))
            server = tenant.servers.get(server_id)
            if not server.image:
                raise AiToolsNovaError("This VM booted from a volume, can't rebuild")
            image_id = image or server.image['id']
            logging.debug("Image to be used has id '%s'" % image_id)
            if not self.dryrun:
                server.rebuild(image=image_id)
                logging.info("Request to rebuild VM '%s' sent" % vmname)
            else:
                logging.info("VM '%s' not rebuilt because dryrun is enabled" % vmname)
        except requests.exceptions.Timeout, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ClientException, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ConnectionRefused, error:
            raise AiToolsNovaError(error)

    def delete(self, fqdn):
        """
        Execute the Nova delete API call to delete a VM.

        :param fqdn: the hostname of the VM to be deleted.
        :raise AiToolsNovaError: in case the deletion API call fails
        """
        vmname = self.__vmname_from_fqdn(fqdn)
        logging.info("Deleting virtual machine '%s'..." % vmname)
        tenant = self.__init_client()
        try:
            server_id = self.__resolve_id(tenant.servers.list(), vmname)
            logging.debug("Server '%s' has id '%s'" % (vmname, server_id))
            if not self.dryrun:
                tenant.servers.get(server_id).delete()
                logging.info("Delete request sent")
            else:
                logging.info("VM '%s' not deleted because dryrun is enabled" % vmname)
        except requests.exceptions.Timeout, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ClientException, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ConnectionRefused, error:
            raise AiToolsNovaError(error)

    def find_image_by_name(self, name):
        tenant = self.__init_client()
        try:
            return self.__resolve_id(tenant.images.list(), name)
        except requests.exceptions.Timeout, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ClientException, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ConnectionRefused, error:
            raise AiToolsNovaError(error)

    def __init_client(self):
        if self.nova is None:
            try:
                self.nova = client.Client(username='', api_key='', project_id='',
                    auth_url='', timeout=self.timeout,
                    session=self.auth_client.session)
            except novaclient.exceptions.ClientException, error:
                raise AiToolsNovaError(error)
            except novaclient.exceptions.ConnectionRefused, error:
                raise AiToolsNovaError(error)
        return self.nova

    def __vmname_from_fqdn(self, fqdn):
        return re.sub("\.cern\.ch$", "", fqdn)

    def __resolve_id(self, collection, resolvable):
        if is_valid_UUID(resolvable):
            return resolvable
        filtered = filter(lambda x: x.name == resolvable, collection)
        if len(filtered) == 0:
            raise AiToolsNovaError("'%s' not found" % resolvable)
        else:
            return filtered[0].id
