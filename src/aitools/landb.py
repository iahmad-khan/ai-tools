#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import logging
import getpass

from suds.client import Client 
from suds.sax.element import Element
from suds.xsd.doctor import ImportDoctor, Import
from suds import WebFault

from aitools.config import LandbConfig
from aitools.common import shortify

from aitools.errors import AiToolsLandbError
from aitools.errors import AiToolsLandbInitError

WSDL_URL = 'https://network.cern.ch/sc/soap/soap.fcgi?v=5&WSDL'
XMLSOAP_SCHEMA_URL = 'http://schemas.xmlsoap.org/soap/encoding/'

class LandbClient():

    def __init__(self, username, host=None, port=None, timeout=None, 
        dryrun=False, deref_alias=False):
        """
        Landb client for interacting with the network database. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured Landb host
        :param port: override the auto-configured Landb port
        :param timeout: override the auto-configured Landb timeout
        :param dryrun: create a dummy client
        :param deref_alias: resolve dns load balanced aliases
        """
        config = LandbConfig()
        self.host = host or config.landb_hostname
        self.port = int(port or config.landb_port)
        self.timeout = int(timeout or config.landb_timeout)
        self.dryrun = dryrun
        self.deref_alias = deref_alias
        self.cache = {}
        self.username = username
        logging.info("This tool talks to LANDB so your password is required")
        self.password = getpass.getpass()
        self.__init_soap_client()

    def __init_soap_client(self):
        self.client = Client(WSDL_URL, 
            doctor=ImportDoctor(Import(XMLSOAP_SCHEMA_URL)), cache=None) 

        try:
            token = self.client.service.getAuthToken(self.username,
                self.password , 'CERN')
        except WebFault, error:
            raise AiToolsLandbInitError(error)
        authTok = Element('token').setText(token)
        auth_header = Element('Auth').insert(authTok)
        self.client.set_options(soapheaders=auth_header)

    def change_responsible(self, fqdn, login, egroup=True):
        if self.dryrun:
            logging.info("Would have changed responsible to '%s'", login)
            return

        hostname = shortify(fqdn)
        try:
            device = self.client.service.getDeviceInfo(hostname)
        except WebFault, error:
            raise AiToolsLandbError(error)

        # Generate a DeviceInput with the new resposible

        # Call deviceUpdate
