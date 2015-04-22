#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import logging
import getpass
import suds

from suds.sax.element import Element
from suds.xsd.doctor import ImportDoctor, Import
from suds import WebFault
from suds import null

from aitools.config import LandbConfig
from aitools.common import shortify

from aitools.errors import AiToolsLandbError
from aitools.errors import AiToolsLandbInitError

WSDL_URL = 'https://network.cern.ch/sc/soap/soap.fcgi?v=5&WSDL'
XMLSOAP_SCHEMA_URL = 'http://schemas.xmlsoap.org/soap/encoding/'

class LandbClient():

    def __init__(self, username, password, host=None, port=None,
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
        self.dryrun = dryrun
        self.deref_alias = deref_alias
        self.username = username
        if not password:
            logging.info("This tool talks to LANDB so your password is required")
            self.password = getpass.getpass()
        else:
            self.password = password
        self.__init_soap_client()

    def __init_soap_client(self):
        self.client = suds.client.Client(WSDL_URL,
            doctor=ImportDoctor(Import(XMLSOAP_SCHEMA_URL)), cache=None)

        try:
            token = self.client.service.getAuthToken(self.username,
                self.password , 'CERN')
        except WebFault, error:
            raise AiToolsLandbInitError(error)
        authTok = Element('token').setText(token)
        auth_header = Element('Auth').insert(authTok)
        self.client.set_options(soapheaders=auth_header)

    def change_responsible(self, fqdn, name, firstname=None):
        logging.debug("Getting object representation...")
        hostname = shortify(fqdn)
        try:
            device = self.client.service.getDeviceInfo(hostname)
        except WebFault, error:
            logging.debug(error)
            raise AiToolsLandbError("getDeviceInfo failed (-v for more info)")

        new_responsible = self.client.factory.create("types:PersonInput")
        if not firstname:
            new_responsible.FirstName = 'E-GROUP'
        else:
            new_responsible.FirstName = firstname.upper()
        new_responsible.Name = name.upper()
        new_responsible.Department = null()
        new_responsible.Group = null()

        logging.debug("Current responsible: %s",  device.ResponsiblePerson)
        logging.debug("New responsible: %s",  new_responsible)
        device.ResponsiblePerson = new_responsible

        if self.dryrun:
            logging.info("Would have changed responsible to '%s'", name)
            return

        logging.debug("Calling deviceUpdate...")
        try:
            response = self.client.service.deviceUpdate(hostname, device)
        except WebFault, error:
            logging.debug(error)
            raise AiToolsLandbError("deviceUpdate failed (-v for more info)")
