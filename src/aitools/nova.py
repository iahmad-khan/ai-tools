import re
import logging
import novaclient.exceptions
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

    def boot(self, fqdn, flavor, image, userdata,
            key_name=None, availability_zone=None):
        vmname = re.sub("\.cern\.ch$", "", fqdn)
        logging.info("Creating virtual machine '%s'..." % vmname)
        tenant = client.Client(self.username, self.password,
            self.tenant_name, 
            auth_url=self.auth_url,
            cacert=CERN_CA_BUNDLE,
            service_type="compute",
            timeout=self.timeout)

        try:
            flavor_id = self.__resolve_id(tenant.flavors.list(), flavor)
            image_id = self.__resolve_id(tenant.images.list(), image)
            if not self.dryrun:
                tenant.servers.create(name=vmname,
                    image=image_id,
                    flavor=flavor_id,
                    userdata=userdata,
                    key_name=key_name,
                    availability_zone=availability_zone)
            else:
                logging.info("VM '%s' not created because dryrun is enabled" % vmname)
                
        except novaclient.exceptions.ClientException, error:
            raise AiToolsNovaError(error)
        except novaclient.exceptions.ConnectionRefused, error:
            raise AiToolsNovaError(error)

    def __resolve_id(self, collection, name):
        filtered = filter(lambda x: x.name == name, collection)
        if len(filtered) == 0:
            raise AiToolsNovaError("'%s' not found" % name)
        else:
            return filtered[0].id
