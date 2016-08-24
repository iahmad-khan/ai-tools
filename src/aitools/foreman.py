#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import logging
import json
import socket
import urllib
import re
import requests
import math

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsForemanError
from aitools.errors import AiToolsForemanNotFoundError
from aitools.errors import AiToolsForemanNotAllowedError
from aitools.common import print_progress_meter, shortify
from aitools.httpclient import HTTPClient
from aitools.config import ForemanConfig
from aitools.common import deref_url

# This is the number of pages that have to be retrieved
# by search_query to consider the query "expensive".
EXP_THOLD = 4

class ForemanClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, dryrun=False, deref_alias=False):
        """
        Foreman client for interacting with the Foreman service. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured Foreman host
        :param port: override the auto-configured Foreman port
        :param timeout: override the auto-configured Foreman timeout
        :param dryrun: create a dummy client
        :param deref_alias: resolve dns load balanced aliases
        """
        fmconfig = ForemanConfig()
        self.host = host or fmconfig.foreman_hostname
        self.port = int(port or fmconfig.foreman_port)
        self.timeout = int(timeout or fmconfig.foreman_timeout)
        self.dryrun = dryrun
        self.deref_alias = deref_alias
        self.cache = {}

    def addhost(self, fqdn, environment, hostgroup, owner,
            managed=False, operatingsystem=None, medium=None,
            architecture=None,
            comment=None, ptable=None, mac=None, ip=None):
        """
        Add a host entry to Foreman.

        :param fqdn: the hostname to add
        :param environment: the initial environment for the host
        :param hostgroup: the initial hostgroup for the host
        :param owner:  the initial owner of the host though will be quickly overriden by the value in LANDB
        :raise AiToolsForemanError: in case the host addition fails
        """
        logging.info("Adding host '%s' to Foreman..." % fqdn)
        payload = {'managed': False, 'name': fqdn}
        payload['environment_id'] = self.__resolve_environment_id(environment)
        payload['hostgroup_id'] = self.__resolve_hostgroup_id(hostgroup)
        payload['owner_type'] = "User"
        payload['owner_id'] = self.__resolve_user_id(owner)
        if comment:
            payload['comment'] = comment
        if managed:
            if any(f is None for f in (operatingsystem, medium,
                architecture, ptable, mac, ip)):
                raise AiToolsForemanError("Missing mandatory params for a managed host")
            payload['managed'] = True
            payload['operatingsystem_id'] = \
                self.__resolve_operatingsystem_id(operatingsystem)
            payload['medium_id'] = self.__resolve_medium_id(medium)
            payload['architecture_id'] = self.__resolve_architecture_id(architecture)
            payload['ptable_id'] = self.__resolve_ptable_id(ptable)
            payload['ip'] = ip
            payload['mac'] = mac
        payload = {'host': payload}

        logging.debug("With payload: %s" % payload)
        if not self.dryrun:
            (code, body) = self.__do_api_request("post", "hosts", data=json.dumps(payload))
            if code == requests.codes.created:
                logging.info("Host '%s' created in Foreman" % fqdn)
            elif code == requests.codes.unprocessable_entity:
                error = ','.join(body['error']['full_messages'])
                raise AiToolsForemanError("addhost call failed (%s)" % error)
            else:
                raise AiToolsForemanError("Unexpected error code (%i) when trying to "
                    "add '%s' to Foreman" % (code, fqdn))
        else:
            logging.info("Host '%s' not added because dryrun is enabled" % fqdn)

    def updatehost(self, host, environment=None, hostgroup=None,
            operatingsystem=None, medium=None, architecture=None,
            comment=None, ptable=None, mac=None, ip=None):
        """
        Updates a host entry in Foreman.

        :param host: host data as returned by GET /api/hosts
        :param environment: the environment for the host ("production")
        :param hostgroup: the hostgroup for the host ("foo/bar")
        :param operatingsystem: the operatingsystem for the host ("SLC 6.6")
        :param medium: the operatingsystem medium for the host ("SLC 6.6")
        :param architecture: the architecture for the host ("x86_64")
        :param comment: the comment for the host
        :param ptable: the ptable for the host ("Kickstart default")
        :param mac: the mac for the host ("11:22:33:44:55:66")
        :param ip: the ip address for the host ("127.0.0.1")
        ...
        :raise AiToolsForemanError: in case the host update fails
        """
        logging.debug("Updating host '%s' in Foreman..." % host['name'])
        payload_keys = ['name', 'environment_id', 'hostgroup_id', 'operatingsystem_id',
                        'medium_id', 'architecture_id', 'comment', 'ptable_id', 'mac', 'ip' ]
        payload = dict((key, host[key]) for key in payload_keys)
        if environment:
            payload['environment_id'] = self.__resolve_environment_id(environment)
        if hostgroup:
            payload['hostgroup_id'] = self.__resolve_hostgroup_id(hostgroup)
        if operatingsystem:
            payload['operatingsystem_id'] = \
                self.__resolve_operatingsystem_id(operatingsystem)
        if medium:
            payload['medium_id'] = self.__resolve_medium_id(medium)
        if architecture:
            payload['architecture_id'] = self.__resolve_architecture_id(architecture)
        if comment:
            payload['comment'] = comment
        if ptable:
            payload['ptable_id'] = self.__resolve_ptable_id(ptable)
        if mac:
            payload['mac'] = mac
        if ip:
            payload['ip'] = ip
        payload = {'host': payload}

        logging.debug("With payload: %s" % payload)
        if not self.dryrun:
            (code, body) = self.__do_api_request("put", "hosts/%s" % host['name'],
                data=json.dumps(payload))
            if code == requests.codes.ok:
                logging.debug("Host '%s' updated" % host['name'])
            elif code == requests.codes.not_found:
                raise AiToolsForemanNotFoundError("Host '%s' not found in Foreman" % host['name'])
            elif code == requests.codes.unprocessable_entity:
                error = ','.join(body['error']['full_messages'])
                raise AiToolsForemanError(error)
            else:
                raise AiToolsForemanError("Unexpected error code (%i) when trying to "
                    "update '%s' in Foreman" % (code, host['name']))
        else:
            logging.info("Host '%s' not updated because dryrun is enabled" % host['name'])

    def delhost(self, fqdn):
        """
        Delete the specified host in Foreman.

        :param fqdn:
        :raise AiToolsForemanNotFoundError: if try to delete machine that doesn't exist
        :raise AiToolsForemanNotAllowedError: if try to delete machine and not allowed
        :raise AiToolsForemanError: for any other error
        """
        if self.dryrun:
            logging.info("Host '%s' not deleted because dryrun is enabled" % fqdn)
            return True
        logging.info("Deleting host '%s' from Foreman..." % fqdn)
        (code, body) = self.__do_api_request("delete", "hosts/%s" % fqdn)
        if code == requests.codes.ok or code == requests.codes.accepted or code == requests.codes.no_content:
            return body
        elif code == requests.codes.not_found:
            raise AiToolsForemanNotFoundError("Host '%s' not found in Foreman" % fqdn)
        elif code == requests.codes.unauthorized:
            raise AiToolsForemanNotAllowedError("Not allowed to delete host '%s' in foreman" % fqdn)
        else:
            raise AiToolsForemanError("Error code '%i' received trying to delete '%s' from foreman" % (code, fqdn))


    def gethost(self, fqdn, toexpand=['hostgroup']):
        """
        Get basic information about a host.

        :param fqdn: the hostname to query
        :return: a parsed JSON dictionary record
        :raise AiToolsForemanError: if the query call failed or the host could not be found
        """
        logging.debug("Getting host '%s' from Foreman..." % fqdn)

        (code, body) = self.__do_api_request("get", "hosts/%s" % fqdn)
        if code == requests.codes.ok:
            for model in toexpand:
                body[model] = self.__resolve_model(model,
                    body["%s_id" % model])
            return body
        elif code == requests.codes.not_found:
            raise AiToolsForemanNotFoundError("Host '%s' not found or not visible "
                "with the presented credentials" % fqdn)
        elif code == requests.codes.unprocessable_entity:
            error = ','.join(body['error']['full_messages'])
            raise AiToolsForemanError("gethost call failed (%s)" % error)
        else:
            raise AiToolsForemanError("Unexpected error code (%i) when getting "
                "'%s' from Foreman" % (code, fqdn))

    def getks(self, ip_address):
        """
        Get the Kickstart file for a given IP address.

        :param ip_address: the IP address to query
        :return: the KS itself
        :raise AiToolsForemanError: if the query call failed or the host could not be found
        """
        logging.info("Getting Kickstart for host with IP '%s' from Foreman..."
            % ip_address)

        (code, body) = self.__do_api_request("get",
            "unattended/provision?spoof=%s" % ip_address, prefix='')
        if code == requests.codes.ok:
            return body
        elif code == requests.codes.not_found:
            raise AiToolsForemanNotFoundError("Host with IP '%s'"
                " not found in Foreman" % ip_address)
        elif code == requests.codes.bad_request:
            # Not very accurate, but it's what Foreman spits out if no KS
            # can be resolved
            raise AiToolsForemanError("Kickstart for host with IP '%s'"
                " not found in Foreman" % ip_address)
        else:
            raise AiToolsForemanError("Error code '%i' received when trying to "
                "get a KS for '%s' from Foreman" % (code, ip_address))

    def getfacts(self, fqdn):
        """
        Get the facts for a host, as seen by Foreman.

        Usage: it is suggested for normal use to fetch the facts from PuppetDB.

        :param fqdn: the hostname to query
        :return: a parsed JSON dictionary of facts
        :raise AiToolsForemanError: if the call failed or the host could not be found
        """
        logging.info("Getting facts for host '%s' from Foreman..." % fqdn)

        (code, body) = self.__do_api_request("get", "hosts/%s/facts/?per_page=500" % fqdn)
        if code == requests.codes.ok:
            return body
        elif code == requests.codes.not_found:
            raise AiToolsForemanNotFoundError("Host '%s' (or facts) not found in Foreman" % fqdn)
        elif code == requests.codes.unprocessable_entity:
            raise AiToolsForemanError("getfacts call failed (Unprocessable entity)")
        else:
            raise AiToolsForemanError("Error code '%i' received when trying to "
                "get facts for host '%s'' Foreman" % (code, fqdn))

    def renamehost(self, oldfqdn, newfqdn):
        """
        Rename the specified host in Foreman.

        :param oldfqdn: the current hostname
        :param newfqdn: the new hostname
        :raise AiToolsForemanError: if the rename call failed or if the host was not found
        """
        logging.info("Renaming host '%s' to '%s' in Foreman" % (oldfqdn,newfqdn))
        payload = {"host": {"name": newfqdn}}
        if not self.dryrun:
            (code, body) = self.__do_api_request("put", "hosts/%s" % oldfqdn,
                                data=json.dumps(payload))
            if code == requests.codes.ok:
                logging.info("Rename '%s' to '%s' OK in Foreman" % (oldfqdn,newfqdn))
            elif code == requests.codes.not_found:
                raise AiToolsForemanNotFoundError("Host '%s' not found in Foreman" % oldfqdn)
            elif code == requests.codes.unprocessable_entity:
                raise AiToolsForemanError("Rename of '%s' failed. Is '%s' already registered?"
                    % (oldfqdn, newfqdn))
            else:
                raise AiToolsForemanError("An error occurred when changing host name to '%s'" % newfqdn)

            # update the certname on the new host name to ensure we have at least one aufit record on the
            # new host - needed to make YAML generation work
            payload = {"host": {"certname": newfqdn}}
            (code, body) = self.__do_api_request("put", "hosts/%s" % newfqdn,
                                data=json.dumps(payload))
            if code == requests.codes.ok:
                logging.info("Updating certname record for new host %s" % (newfqdn))
            else:
                logging.warn("Could not update certname for new host %s" % (newfqdn))


            # Now fetch and updated IPMI interface
            (code, body) = self.__do_api_request("get", "hosts/%s/interfaces" % newfqdn)

            if body['subtotal'] == 0:
                logging.info("No IPMI interfaces to update for new host %s" % (newfqdn))
                return
            interface = None
            for result in body['results']:
                if 'provider' in result and result["provider"] == "IPMI":
                    interface = result
                    break
            if not interface:
                logging.info("No IPMI interfaces to update for new host %s" % (newfqdn))
                return

            # Don't rename special IPMI interfaces, see AI-4389
            if interface['name'] != ("%s-ipmi.cern.ch" % shortify(oldfqdn)):
                logging.info("Special IPMI interface name, not to be renamed.")
                return

            interface_id = interface["id"]

            new_interface_name = newfqdn.replace(".cern.ch", "-ipmi.cern.ch")

            # Now update the IPMI interface
            payload = {
                "interface": {
                    "name": new_interface_name,
                    "provider": interface["provider"],
                    "type": interface["type"],
                }
            }
            (code, body) = self.__do_api_request("put", "hosts/%s/interfaces/%s" % (newfqdn, interface_id),
                                data=json.dumps(payload))
            if code == requests.codes.ok:
                logging.info("Updated IPMI interface with new name: %s" % (new_interface_name))
            else:
                logging.warn("Could not update IPMI interface with new name: %s" % (new_interface_name))
        else:
            logging.info("Host '%s' not renamed to '%s' because dryrun is enabled" % (oldfqdn, newfqdn,))


    def addhostparameter(self, fqdn, name, value):
        """
        Add a name,value parameter to the specified host in Foreman.

        :param fqdn: the hostanme to add the parameter to.
        :param name: the name of the parameter to add
        :param value: the value of the parameter
        :raise AiToolsForemanError: if the parameter-set call failed or if the host was not found
        """
        logging.info("Adding parameter '%s' to host '%s' with value '%s'..."
                        % (name, fqdn, value))
        payload = {'parameter': {'name' : name, 'value': value}}
        logging.debug("With payload: %s" % payload)

        if not self.dryrun:
            (code, body) = self.__do_api_request("post", "hosts/%s/parameters" % fqdn,
                                data=json.dumps(payload))
            if code == requests.codes.ok:
                logging.info("Parameter '%s' created in Foreman" % name)
            elif code == requests.codes.not_found:
                raise AiToolsForemanNotFoundError("Host '%s' not found in Foreman" % fqdn)
            elif code == requests.codes.unprocessable_entity:
                message = "Foreman returned 'Unprocessable entity'. Does the parameter already exist?"
                if hasattr(body['error'], 'full_messages'):
                    message = ','.join(body['error']['full_messages'])
                raise AiToolsForemanError(message)
        else:
            logging.info("Parameter '%s' not added because dryrun is enabled" % name)

    def __create_single_hostgroup(self, hostgroup, parent_id=None, parent_name=None):
        """
        Creates single hostgroup with selected parent hostgroup.
        """

        if parent_name:
            hostgroup_fullname = "%s/%s" % (parent_name, hostgroup)
        else:
            hostgroup_fullname = hostgroup

        logging.info("Creating hostgroup '%s'..." % hostgroup_fullname)
        payload = {'hostgroup': {'name': hostgroup}}
        if parent_id:
            payload['hostgroup']['parent_id'] = parent_id
        logging.debug("With payload: %s" % payload)

        if self.dryrun:
            logging.info("Hostgroup '%s' not created because dryrun is enabled" %
                hostgroup)
            return None

        (code, body) = self.__do_api_request("post", "hostgroups",
                            data=json.dumps(payload))
        if code == requests.codes.created:
            logging.info("Hostgroup '%s' created in Foreman" % hostgroup_fullname)
            return body['id']
        elif code == requests.codes.unprocessable_entity:
            raise AiToolsForemanNotAllowedError(
                "Hostgroup '%s' already exists in Foreman" % hostgroup_fullname)
        else:
            raise AiToolsForemanError(
                "Could not create hostgroup '%s' in Foreman" % hostgroup_fullname)

    def __create_hostgroup_hierarchy(self, tree, create_parents):
        """
        Recursively go up in the tree until the already created hostgroup
        and create needed hostgroups if create_parents is set to True,
        otherwise try to create low-level hostgroup.
        """

        if len(tree) == 1:
            return self.__create_single_hostgroup(tree[-1])

        parent_name = '/'.join(tree[ :-1])
        try:
            parent_id = self.__resolve_hostgroup_id(parent_name)
        except AiToolsForemanNotFoundError:
            if not create_parents:
                raise AiToolsForemanNotAllowedError(
                    "Could not create hostgroup '%s' in Foreman because some"
                    " parts of the hostgroup hierarchy (%s) do not exist"
                    " (use -p to create hostgroups recursively)" %
                    (tree[-1], '/'.join(tree[ :-1])))

            parent_id = self.__create_hostgroup_hierarchy(tree[ :-1], create_parents)

        return self.__create_single_hostgroup(tree[-1], parent_id, parent_name)

    def createhostgroup(self, hostgroup, parents=False):
        """
        Create new hostgroup. Parents are created recursively as needed if
        option parents is enabled.
        :param hostgroup: the name of the hostgroup to be created
        :param parents: if True - creates needed parents if they don't exist
        :raise AiToolsForemanNotAllowedError: the hostgroup exists already
        or cannot recreate the whole tree due to --parents restriction
        :raise AiToolsForemanError: if the operation failed
        :return: The id of the hostgroup created, or None if dry run is enabled
        """

        tree = hostgroup.strip('/').split('/')
        return self.__create_hostgroup_hierarchy(tree, parents)


    def __traverse_hostgroup_for_deletion(self, hostgroup, candidates, recursive):
        """
        Returns a list of hostgroups to be deleted.
        Exception AiToolsForemanNotAllowedError will be raised if hostgroups
        with hosts are found.
        If recursive is set to False and hostgroup has children hostgroups -
        exception AiToolsForemanNotAllowedError will be raised.
        """

        hgid = self.__resolve_hostgroup_id(hostgroup)
        if not hgid:
            raise AiToolsForemanNotFoundError("Hostgroup '%s' not found "
                                              "in Foreman" % hostgroup)

        logging.debug("Checking if hostgroup '%s' has any hosts..." % hostgroup)
        body = self.search_query('hosts', 'hostgroup_fullname = %s' % hostgroup)
        hosts = [r['name'] for r in body]

        if hosts:
            raise AiToolsForemanNotAllowedError(
                "Hostgroup '%s' can't be removed as it contains hosts" % hostgroup)

        logging.debug("Checking if hostgroup '%s' has any children..." % hostgroup)
        body = self.search_query('hostgroups', '%s/' % hostgroup)
        children = [r['title'] for r in body if r['parent_id'] == hgid]

        if children and not recursive:
            raise AiToolsForemanNotAllowedError(
                "Hostgroup '%s' can not be removed since it contains children "
                "hostgroups. Use --recursive option" % hostgroup)

        for ch in children:
            self.__traverse_hostgroup_for_deletion(ch, candidates, recursive)

        candidates.append(hostgroup)

        return candidates

    def __remove_single_hostgroup(self, hostgroup):
        """
        Removes single hostgroup by provided name of the hostgroup.
        """

        logging.info("Removing hostgroup '%s'..." % hostgroup)

        hgid = self.__resolve_hostgroup_id(hostgroup)
        (code, body) = self.__do_api_request("delete",
                                             "hostgroups/%s" % (hgid))

        if code != requests.codes.ok:
            raise AiToolsForemanError("Could not delete hostgroup '%s'" % hostgroup)

        logging.info("Hostgroup '%s' removed" % hostgroup)

        return body['name']

    def delhostgroup(self, hostgroup, recursive=False):
        """
        Remove specified hostgroup and if recursive option is enabled - all
        children hostgroups.
        If the hostgroup or any children hostgroup
        possesses hosts - operation fails. If it possesses children hostgroups
        and recursive option is not specified - operation fails.
        :param hostgroup: the name of the hostgroup to be deleted
        :param recursive: if True - allows to remove children hostgroups
        :raise AiToolsForemanNotFoundError: if subtree contains hosts or 
        hostgroups which cannot be removed
        :raise AiToolsForemanError: if operation failed
        :return: the name of the highest removed hostgroup in the hierarchy
        """

        candidates = self.__traverse_hostgroup_for_deletion(hostgroup.strip('/'), [], recursive)

        if self.dryrun:
            logging.info("Hostgroup '%s' was not removed because dryrun is enabled" %
                hostgroup)
            logging.info("I would have removed: %s" % ', '.join(candidates))
            return None

        name_removed = []
        for hg in candidates:
            name_removed.append(self.__remove_single_hostgroup(hg))

        return name_removed[-1]

    def gethostgroupparameters(self, hostgroup):
        """
        Get all parameters for the given hostgroup.
        :param hostgroup: the hostgroup to query
        :return: a dictionary of parameters
        """
        logging.info("Getting hostgroup parameters for '%s' from Foreman..." % hostgroup)

        logging.info("Resolving ID for hostgroup '%s'" % hostgroup)
        hgid = self.__resolve_hostgroup_id(hostgroup)

        (code, body) = self.__do_api_request("get", "hostgroups/%s/parameters" % hgid)
        if code == requests.codes.ok:
            params = body['results']
            return params
        elif code == requests.codes.not_found:
            raise AiToolsForemanNotFoundError("Hostgroup '%s' not found in Foreman" % hostgroup)
        elif code == requests.codes.unprocessable_entity:
            raise AiToolsForemanError("gethostgroupparamters call failed")

    def addhostgroupparameter(self, hostgroup, name, value):
        """
        Add a name,value parameter to the specified host in Foreman.

        :param hostgroup: the hostgroup to add the parameter to.
        :param name: the name of the parameter to add
        :param value: the value of the parameter
        :raise AiToolsForemanNotFoundError: if the hostgroup was not found
        :raise AiToolsForemanError: if the parameter-set call failed
        """

        logging.info("Resolving ID for hostgroup '%s'" % hostgroup)
        hgid = self.__resolve_hostgroup_id(hostgroup)

        logging.info("Checking for existing parameter '%s' on hostgroup '%s'" % (name, hostgroup))
        params = self.gethostgroupparameters(hostgroup)
        ids = [(p['id'], p['value']) for p in params if p['name'] == name]

        if ids:
            # param exists, use PUT on that ID
            logging.info("Updating parameter '%s' to hostgroup '%s' to value '%s' (old value: '%s')..."
                            % (name, hostgroup, value, ids[0][1]))
            payload = {'parameter': {'name' : name, 'value': value}}
            logging.debug("With payload: %s" % payload)

            if not self.dryrun:
                (code, body) = self.__do_api_request("put", "hostgroups/%s/parameters/%s" % (hgid, ids[0][0]),
                                    data=json.dumps(payload))
                if code == requests.codes.ok:
                    logging.info("Parameter '%s' updated in Foreman" % name)
                elif code == requests.codes.not_found:
                    raise AiToolsForemanNotFoundError("HostgroupID '%s' not found in Foreman" % hgid)
            else:
                logging.info("Parameter '%s' not added because dryrun is enabled" % name)

        else:
            # param does not exist, use new POST
            logging.info("Adding parameter '%s' to hostgroup '%s' with value '%s'..."
                            % (name, hostgroup, value))
            payload = {'parameter': {'name' : name, 'value': value}}
            logging.debug("With payload: %s" % payload)

            if not self.dryrun:
                (code, body) = self.__do_api_request("post", "hostgroups/%s/parameters" % hgid,
                                    data=json.dumps(payload))
                if code == requests.codes.ok:
                    logging.info("Parameter '%s' created in Foreman" % name)
                elif code == requests.codes.not_found:
                    raise AiToolsForemanNotFoundError("HostgroupID '%s' not found in Foreman" % hgid)
            else:
                logging.info("Parameter '%s' not added because dryrun is enabled" % name)

    def power_operation(self, fqdn, operation):
        """
        Send an IPMI power command to the host via the Foreman BMC proxy.

        Allowed values are:

         - 'on' or 'start' - power up the node
         - 'off; or 'stop' - power down the node
         - 'soft' or 'reboot' - ACPI soft reboot
         - 'cycle' or 'reset' - Hard power cycle
         - 'state' or 'status' - Return the power status

        :param fqdn: host to send the command to.
        :param operation: operation to send.
        :return: the current power status
        """
        logging.info("Executing '%s' on host '%s'" % (operation, fqdn))
        payload = {'power_action': operation}
        logging.debug("With payload: %s" % payload)

        if not self.dryrun:
            return self.__do_api_request("put", "hosts/%s/power" % fqdn,
                                data=json.dumps(payload))
        else:
            logging.info("Power operation on '%s' cancelled because dryrun is enabled" % fqdn)
            return (requests.codes.ok, {'power': 'dryrun'})


    def get_ipmi_interface(self, fqdn):
        try:
          code, response = self.__do_api_request('get',
            "hosts/%s/interfaces" % (fqdn))
          if code == requests.codes.ok:
            for interface in response['results']:
                if interface['name'][-13:] == "-ipmi.cern.ch":
                    return interface
            return None
          else:
            error_message = """Action: check if host %s and its ipmi interface exist in Foreman. [%d, %s]"""\
                             % (fqdn, code, response["error"]["message"])
            raise AiToolsForemanNotFoundError(error_message)
        except AiToolsHTTPClientError, error:
          raise AiToolsForemanError(error)


    def get_ipmi_interface_id(self, fqdn):
        try:
          interface = self.get_ipmi_interface(fqdn)
          return interface['id'] if interface is not None else None
        except (AiToolsForemanNotFoundError, AiToolsForemanError):
          raise


    def add_ipmi_interface(self, host_fqdn, ipmi_fqdn, mac, username, password, ipmi_ip=None):
        # Implementing this as the public API does not support
        # adding IPMI interfaces with the host
        payload = {'name': ipmi_fqdn,
          'ip': ipmi_ip or socket.gethostbyname(ipmi_fqdn),
          'mac':mac,
          'username': username,
          'password': password,
          'type': "Nic::BMC",
          'provider': 'IPMI',
        }

        try:
          code, response = self.__do_api_request('post',
            "hosts/%s/interfaces" % host_fqdn,
            json.dumps(payload))
          if code == requests.codes.created:
            logging.info("%s added" % payload['name'])
          else:
            raise AiToolsForemanError("%d: %s" % (code, response))

        except AiToolsHTTPClientError, error:
          raise AiToolsForemanError(error)


    def rename_ipmi_interface_name(self, fqdn, new_ipmi_intf_fqdn = None):
        # If new_ipmi_intf_fqdn is not mentioned,
        # it will be generated from the host fqdn
        if not new_ipmi_intf_fqdn:
          new_ipmi_intf_fqdn = fqdn.replace(".cern.ch", "-ipmi.cern.ch")
        ipmi_interface_id = self.get_ipmi_interface_id(fqdn)
        if ipmi_interface_id is None:
          raise AiToolsForemanError("Action: add the IPMI interface for %s" % fqdn)
        payload = { 'name': new_ipmi_intf_fqdn }
        try:
          code, response = self.__do_api_request('put',
            "hosts/%s/interfaces/%s" % (fqdn, ipmi_interface_id),
            json.dumps(payload))
          if code == requests.codes.ok:
            logging.info("IPMI interface renamed for device %s to %s" % (fqdn, payload['name']))
          else:
            raise AiToolsForemanError("%d: %s" % (code, response))
        except AiToolsHTTPClientError, error:
          raise AiToolsForemanError(error)


    def change_ipmi_credentials(self, fqdn, username, password):
        ipmi_interface = self.get_ipmi_interface(fqdn)
        payload = {
          'name': ipmi_interface['name'],
          'ip': ipmi_interface['ip'],
          'mac': ipmi_interface['mac'],
          'username': username,
          'password': password,
          'provider': ipmi_interface['provider'],
          'type': ipmi_interface['type'],
        }
        if ipmi_interface is None:
          logging.error("Unable to find the ID of the IPMI interface in Foreman")
          raise AiToolsForemanNotFoundError("Unable to find the ID of the IPMI interface in Foreman")
        try:
          code, response = self.__do_api_request('put',
            "hosts/%s/interfaces/%s" % (fqdn, ipmi_interface['id']),
            json.dumps(payload))
          if code == requests.codes.ok:
            logging.info("IPMI credentials changed for %s" % payload['name'])
          else:
            raise AiToolsForemanError("%d: %s" % (code, response))

        except AiToolsHTTPClientError, error:
          raise AiToolsForemanError(error)


    def get_ipmi_credentials(self, fqdn):
        ipmi_interface_id = self.get_ipmi_interface_id(fqdn)
        try:
          code, response = self.__do_api_request('get',
            "hosts/%s/interfaces/%s" % (fqdn, ipmi_interface_id))
          if code == requests.codes.ok:
            try:
              return response['username'], response['password']
            except KeyError:
              raise AiToolsForemanError('Username and password not found in the interface')
          else:
            raise AiToolsForemanError("%d: %s" % (code, response))

        except AiToolsHTTPClientError, error:
          raise AiToolsForemanError(error)


    def get_environment_by_name(self, name):
        return self.__get_model_by_name('environment', name)

    def __get_model_by_name(self, model, name):
        logging.debug("Requesting %s '%s' from Foreman" % (model, name))

        (code, body) = self.__do_api_request("get", "%ss/%s" % (model, name))
        if code == requests.codes.ok:
            logging.debug("Found: %s" % body)
            return body[model]
        elif code == requests.codes.not_found:
            raise AiToolsForemanNotFoundError("%s '%s' not found in Foreman" % \
                    (model, name))

    def __resolve_environment_id(self, name):
        return self.__resolve_model_id('environment', name)

    def __resolve_hostgroup_id(self, name):
        return self.__resolve_model_id('hostgroup', name, search_key='label')

    def __resolve_user_id(self, name):
        return self.__resolve_model_id('user', name, search_key='login')

    def __resolve_architecture_id(self, name):
        return self.__resolve_model_id('architecture', name)

    def __resolve_ptable_id(self, name):
        return self.__resolve_model_id('ptable', name)

    def __resolve_medium_id(self, name):
        return self.__resolve_model_id('medium', name)

    def __resolve_operatingsystem_id(self, fullname):
        match_object = re.match(r'(?P<name>\S+?)\s+(?P<major>\d+).(?P<minor>\d+)',
            fullname)
        if not match_object:
            raise AiToolsForemanError("Couldn't resolve operating system name")
        try:
            return self.__resolve_model_id('operatingsystem',
                match_object.group('name'),
                results_filter=lambda x: x['title'] == fullname)
        except AiToolsForemanNotFoundError, error:
            # This is necessary to avoid misleading the user showing just
            # the OS name when nothing has been found
            raise AiToolsForemanNotFoundError("Operatingsystem '%s' not found" %
                fullname)

    def __resolve_model_id(self, modelname, value, results_filter=None,
                            search_key="name",
                            value_filter=None):
        cache_key = '%s_%s_id' % (modelname, value)
        if cache_key in self.cache:
            logging.debug("'%s' found in cache" % cache_key)
            return self.cache[cache_key]
        else:
            logging.debug("Asking Foreman for %s '%s'" %
                (modelname, value))
            search_string_value = value
            if value_filter is not None:
                search_string_value = value_filter(value)
            search_string = "%s=\"%s\"" % (search_key, search_string_value)
            model_endpoint = "%ss" % modelname
            if modelname == 'medium':
                model_endpoint = "media"
            results = self.search_query(model_endpoint, search_string)
            if results_filter:
                results = filter(results_filter, results)
            if not results:
                raise AiToolsForemanNotFoundError("%s '%s' not found" %
                    (modelname, value))
            if len(results) > 1:
                raise AiToolsForemanError("Multiple choices for %s lookup" % modelname)
            self.cache[cache_key] = results[0]['id']
            return results[0]['id']

    def __resolve_model(self, modelname, model_id):
        cache_key = '%s_%s' % (modelname, model_id)
        if cache_key in self.cache:
            logging.debug("'%s' found in cache" % cache_key)
            return self.cache[cache_key]
        else:
            logging.debug("Asking Foreman for %s with id '%s'" %
                (modelname, model_id))
            (code, body) = self.__do_api_request("get", "%ss/%s" % (modelname, model_id))
            if code == requests.codes.ok:
                self.cache[cache_key] = body
                return body
            elif code == requests.codes.not_found:
                raise AiToolsForemanError("Model '%s' not found in Foreman" % modelname)
            elif code == requests.codes.unprocessable_entity:
                error = ','.join(body['error']['full_messages'])
                raise AiToolsForemanError("__resolve_model_name call failed (%s)" % error)

    def search_query(self, model, search_string):
        query_string = urllib.urlencode({'search': search_string})
        page = 1
        results = []
        expensive_query = False
        while page == 1 or page <= math.ceil(payload['subtotal']/float(payload['per_page'])):
            url = "%s/?%s&page=%d" % (model, query_string, page)
            (code, payload) = self.__do_api_request("get", url)
            if code == requests.codes.ok:
                if page == 1 and payload['subtotal'] > EXP_THOLD * payload['per_page']:
                    logging.warn("Crikey! That's an expensive query! this might take a while...")
                    expensive_query = True
                if expensive_query:
                    print_progress_meter(page,
                        math.ceil(payload['subtotal']/float(payload['per_page'])))
                results.extend(payload['results'])
                page = page + 1
            else:
                msg = "Foreman didn't return a controlled status code when looking up %s" \
                    % model
                raise AiToolsForemanError(msg)
        if expensive_query:
            print_progress_meter(1, 1, new_line=True)
        return results

    def __do_api_request(self, method, url, data=None, prefix="api/"):
        url = "https://%s:%u/%s%s" % (self.host, self.port, prefix, url)
        if self.deref_alias:
            url = deref_url(url)
        # Yes, Foreman is stupid
        headers = {'User-Agent': 'ai-tools',
            'Content-type': 'application/json',
            'Accept': 'application/json, version=2'}

        try:
            code, response = super(ForemanClient, self).do_request(method, url, headers, data)
            body = response.text
            if code == requests.codes.unauthorized or code == requests.codes.forbidden:
                raise AiToolsForemanNotAllowedError("Unauthorized when trying '%s' on '%s'" % (method, url))
            if re.match('application/json', response.headers['content-type']):
                body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsForemanError(error)
