# Nacho Barrientos <nacho.barrientos@cern.ch>
#
# Disclaimer: This is the ugliest code I've ever written.
# AIMS does not have any Python API, and even worse,
# aims2client returns always zero, no matter if the
# requested operation failed or not.

import logging
import os
import re
import time
from subprocess import Popen, PIPE

from aitools.common import shortify

from aitools.errors import AiToolsAimsError

A2C_BIN_PATH = "/usr/bin/aims2client"
AIMS_DEFAULT_KOPTS = ['text', 'network', 'ks', 'ksdevice=bootif',
    'latefcload', 'nodmraid', 'console=tty0']

class AimsClient(object):
    def __init__(self, dryrun=False):
        self.dryrun = dryrun

    def addhost(self, fqdn, operatingsystem, architecture,
            enc, ksfilepath, user_kopts=None):
        """
        Registers a host in AIMS for installation.

        :param enc: Hash of host parameters coming from the ENC
        :param ksfilepath: disk location of the KS file to be uploaded
        :param user_kopts: Set of additional kernel options to be passed
        """
        kopts = []
        logging.info("Uploading KS for host '%s' to AIMS..." % fqdn)

        if 'hwdbkopts' in enc and enc['hwdbkopts'] != "none":
            kopts.extend(re.split(r'\s+', enc['hwdbkopts']))
            logging.debug("Kernel options coming from Foreman: %s" % kopts)

        if user_kopts is not None:
            kopts.extend(re.split(r'\s+', user_kopts))

        kopts.extend(AIMS_DEFAULT_KOPTS)
        logging.debug("Final kernel options: %s" % " ".join(kopts))

        target = self._translate_foreman_os_to_target(operatingsystem,
            architecture)

        args = ["addhost", "--pxe",
            "--hostname", shortify(fqdn),
            "--name", target,
            "--kickstart", ksfilepath,
            "--kopts", "%s" % " ".join(kopts)]
        logging.debug("Argument string to be sent to AIMS: %s" % args)

        if self.dryrun:
            logging.info("addhost not called because dryrun is enabled")
            return target

        out, returncode = self._exec(args)
        logging.info(out.strip())
        logging.info("KS for host '%s' uploaded to AIMS." % fqdn)
        return target

    def pxeon(self, fqdn, pxetarget):
        """
        Makes sure that the host has the PXE flag on in AIMS

        :param pxetarget: Boot target for the concerning host (e.g. "SLC65")
        """
        logging.info("Making sure PXE is ON for host '%s'..." % fqdn)
        args = ["pxeon", shortify(fqdn), pxetarget]
        if self.dryrun:
            logging.info("pxeon not called because dryrun is enabled")
            return

        out, returncode = self._exec(args)
        logging.info(out.strip())

    def showhost(self, fqdn):
        """ Gets what AIMS has to say about a given host. """
        logging.debug("Getting info for host '%s'..." % fqdn)
        args = ["showhost", shortify(fqdn), "--full"]
        out, returncode = self._exec(args)
        return out

    def wait_for_readiness(self, fqdn, attempts=12, waittime=10):
        """
        Waits a given number of attempts for the sync state to be
        correct with a wait time in between.
        """

        logging.info("Sync waiting loop for host '%s' started" % fqdn)
        if self.dryrun:
            logging.info("Nothing to wait for because dryrun is enabled")
            return True

        for attempt in range(0, attempts):
            hoststatus = self.showhost(fqdn)
            statuses = []
            for line in hoststatus.splitlines():
                match = re.match(r"^PXE boot synced:\s+(?P<status>[yYnN])", line)
                if match:
                    logging.debug("Found a boot synced statement (%s)" % line)
                    statuses.append(match.group('status'))

            if re.match(r"^[yY]+$", "".join(statuses)):
                logging.info("Sync status for '%s' is set to Y on all interfaces"
                    % fqdn)
                return
            else:
                logging.debug("Sync status is not Y for all interfaces")
                logging.debug("Sleeping for %d seconds..." % waittime)
                time.sleep(waittime)

        logging.error(hoststatus.strip())
        raise AiToolsAimsError("Sync status is not Y after all the attempts")

    def _translate_foreman_os_to_target(self, operatingsystem, architecture):
        """
        Translates OS information coming from foreman (OS name, major version
        and minor version) into boot targets known to AIMS.
        """
        if 'name' not in operatingsystem:
            raise AiToolsAimsError("Unable to find OS name")
        if 'name' not in architecture:
            raise AiToolsAimsError("Unable to find architecture name")

        try:
            major = int(operatingsystem['major'])
            minor = int(operatingsystem['minor'])
        except (ValueError, KeyError):
            raise AiToolsAimsError("OS major/minor not defined or bogus")

        if operatingsystem['name'] == "SLC":
            target_os = "SLC%s%s" % (major, minor)
        # It's not clear yet that minor versions will be supported
        # so for the moment we map ignoring the minors.
        elif operatingsystem['name'] == "CentOS":
            target_os = "CC%s" % major
        elif operatingsystem['name'] == "RedHat":
            if major == 5:
                target_os = "RHES_5_U%s" % minor
            else:
                target_os = "RHEL%s_U%s" % (major, minor)
        elif operatingsystem['name'] == "Fedora":
            target_os = "FEDORA%s" % major
        else:
            raise AiToolsAimsError("There's no PXE target for '%s'"
                % operatingsystem['name'])

        pxetarget = "%s_%s" % (target_os, architecture['name'].upper())
        logging.debug("%s translated into %s" % (operatingsystem, pxetarget))
        return pxetarget

    def _exec(self, args):
        """ This is the mega sophisticated interface to AIMS. """
        args = [A2C_BIN_PATH] + args
        logging.debug("Executing %s" % args)
        aims = Popen(args, stdout=PIPE, stderr=PIPE)
        (details, err)  = aims.communicate()
        returncode = aims.returncode
        if returncode != 0:
            raise AiToolsAimsError("%s returned non-zero status (%s)" % \
                (args, err.strip()))
        if len(err) > 0:
            raise AiToolsAimsError("Aims2client failed (%s)" % err.strip())
        return (details, returncode)