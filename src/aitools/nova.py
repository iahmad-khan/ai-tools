#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import re
import logging
import novaclient.exceptions
import requests
from novaclient.v1_1 import client

from aitools.errors import AiToolsNovaError
from aitools.common import CERN_CA_BUNDLE

class NovaClient():
    def __init__(self, auth_url, username, password,
            tenant_name, timeout, dryrun):
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.tenant_name = tenant_name
        self.timeout = timeout
        self.dryrun = dryrun

    def boot(self, fqdn, flavor, image, userdata, meta,
            key_name=None, availability_zone=None):
        vmname = self.__vmname_from_fqdn(fqdn)
        logging.info("Creating virtual machine '%s'..." % vmname)
        tenant = self.__init_client()
        try:
            flavor_id = self.__resolve_id(tenant.flavors.list(), flavor)
            logging.debug("Flavor '%s' has id '%s'" % (flavor, flavor_id))
            image_id = self.__resolve_id(tenant.images.list(), image)
            logging.debug("Image '%s' has id '%s'" % (image, image_id))
            if not self.dryrun:
                tenant.servers.create(name=vmname,
                    image=image_id,
                    flavor=flavor_id,
                    userdata=userdata,
                    meta=meta,
                    key_name=key_name,
                    availability_zone=availability_zone)
            else:
                logging.info("VM '%s' not created because dryrun is enabled" % vmname)
        except requests.exceptions.Timeout, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ClientException, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ConnectionRefused, error:
            raise AiToolsNovaError(error)

    def delete(self, fqdn):
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

    def __init_client(self):
        try:
            return client.Client(self.username, self.password,
                    self.tenant_name,
                    auth_url=self.auth_url,
                    cacert=CERN_CA_BUNDLE,
                    service_type="compute",
                    timeout=self.timeout)
        except novaclient.exceptions.ClientException, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ConnectionRefused, error:
            raise AiToolsNovaError(error)

    def __vmname_from_fqdn(self, fqdn):
        return re.sub("\.cern\.ch$", "", fqdn)

    def __resolve_id(self, collection, name):
        filtered = filter(lambda x: x.name == name, collection)
        if len(filtered) == 0:
            raise AiToolsNovaError("'%s' not found" % name)
        else:
            return filtered[0].id
