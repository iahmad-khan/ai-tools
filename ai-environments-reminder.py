#!/usr/bin/env python
# Authors:
#  Nacho Barrientos <nacho.barrientos@cern.ch>

# Exit codes:
#  0 all operations succeeded
#  2 bad command line
#  3 Kerberos TGT not found or expired

import os
import sys
import logging
import argparse
import socket
import json
import requests
import krbV
import urllib
import yaml
import re
import smtplib
import datetime
import dateutil.parser
from string import Template
from email.mime.text import MIMEText
from requests_kerberos import HTTPKerberosAuth

DEFAULT_LOGGING_LEVEL=logging.INFO
DEFAULT_FOREMAN_TIMEOUT = 15
DEFAULT_FOREMAN_HOSTNAME = "judy.cern.ch"
DEFAULT_FOREMAN_PORT = 8443
CERN_CA_BUNDLE = "/etc/ssl/certs/CERN-bundle.pem"

DEFAULT_ENVIRONMENTS_PATH = "it-puppet-environments"
ENVIRONMENTS_BLACKLIST = ['production.yaml', 'qa.yaml', 'migration_ai1437.yaml']

CACHE = {}

class LocalError(Exception):
    pass

class ForemanError(Exception):
    pass

class ForemanElementNotFound(Exception):
    pass

def configure_logging():
    """Configures application log level based on cmdline arguments"""
    logging_level = DEFAULT_LOGGING_LEVEL
    if args.verbose:
        logging_level = logging.DEBUG
    logging.basicConfig(level=logging_level, format="%(message)s")

def verify_kerberos():
    context = krbV.default_context()
    ccache = context.default_ccache()
    try:
        ccache.principal()
    except krbV.Krb5Error:
        raise LocalError("Kerberos principal not found")

def parse_cmdline_args():
    """Parses and validates cmdline arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
        action="store_true",
        help="Be chatty")
    parser.add_argument('-d', '--dryrun',
        action="store_true",
        help="Do not send emails")
    parser.add_argument('--foreman-timeout', type=int,
        help="Timeout for Foreman operations (default: %s seconds)" % \
        DEFAULT_FOREMAN_TIMEOUT,
        default = DEFAULT_FOREMAN_TIMEOUT)
    parser.add_argument('--foreman-hostname',
        help="Foreman hostname (default: %s)" % DEFAULT_FOREMAN_HOSTNAME,
        default=DEFAULT_FOREMAN_HOSTNAME)
    parser.add_argument('--foreman-port', type=int,
        help="Foreman Kerberos port (default: %s)" % DEFAULT_FOREMAN_PORT,
        default=DEFAULT_FOREMAN_PORT)
    parser.add_argument('-e', '--environments', type=str,
        default=DEFAULT_ENVIRONMENTS_PATH,
        help="Clone of it-puppet-environments")
    args = parser.parse_args()
    return args

def send_email_environment_empty(environment, addr):
    subject = "Information about your environment '%s'" % environment
    template = Template("""Hi,

We believe that the Puppet environment '$environment' is not being used,
given that according to Foreman it has no hosts associated to it.

Unused environments waste space in the Puppet masters and make the sync
process slower. If you don't need the environment anymore (because for
instance you're done developing your new feature or your bugfix) please
get rid of it by following this procedure:

    http://cern.ch/go/6M6P

Don't forget to also remove all the referenced branches living in the
repositories that have overrides.

Thanks!

Jens (CERN's Puppet librarian)""")
    logging.info("Sending email about environment '%s' to '%s'" % \
        (environment, addr))
    body = template.substitute(environment=environment)
    send_email(subject, addr, None, body)

def send_email(subject, to_addr, cc_addr, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = "noreply@cern.ch"
        msg['To'] = to_addr
        if cc_addr is not None:
            msg['CC'] = cc_addr
        server = smtplib.SMTP('localhost')
        server.sendmail("noreply@cern.ch", (to_addr,), msg.as_string())
        logging.debug("Email sent to %s" % to_addr)
    except smtplib.SMTPException, error:
        raise LocalError("Failed to send mail to '%s' (%s)" %
            (to_addr, error))

def foreman_query(path):
    if path in CACHE:
        logging.debug('%s is cached' % path)
        return CACHE[path]
    url="https://%s:%u/api/%s" % \
        (args.foreman_hostname, args.foreman_port, path)
    logging.debug("Issuing GET on %s" % url)
    headers = {'Content-type': 'application/json',
        'Accept': 'application/json, version=2',
        'User-Agent': 'ai-environments-reminder'}
    logging.debug("With headers: %s" % headers)
    try:
        response = requests.get(url, timeout=args.foreman_timeout,
            headers=headers, auth=HTTPKerberosAuth(),
            verify=CERN_CA_BUNDLE, allow_redirects=True)
        if response.status_code == requests.codes.ok:
            try:
                output = json.loads(response.text)
                CACHE[path] = output
                return output
            except ValueError:
                logging.error("Failed to parse JSON")
        elif response.status_code == requests.codes.forbidden or \
            response.status_code == requests.codes.unauthorized:
                raise ForemanError("Authentication failed (expired or non-existent TGT?)")
        elif response.status_code == requests.codes.not_found:
            raise ForemanElementNotFound("%s not found in Foreman" % path)
        elif response.status_code == requests.codes.internal_server_error:
            raise ForemanError("Foreman's ISE. Open a bug against Foreman")
        else:
            raise ForemanError("Uncontrolled status code (%s), please report a bug" %
                response.status_code)
    except requests.exceptions.ConnectionError, error:
        raise ForemanError("Connection error (%s)" % error)
    except requests.exceptions.Timeout, error:
        raise ForemanError("Connection timeout")

def get_environment(environment):
    try:
        environment = foreman_query('environments/%s' % environment)
    except ForemanElementNotFound:
        logging.error("Environment '%s' not found or not visible with the presented \
credentials" % environment)
        return None
    environment = environment['environment']
    return environment

def read_environment_definition(environment):
    try:
        path = args.environments + "/%s" % environment
        logging.debug("Reading environment from %s" % path)
        return yaml.load(open(path, 'r'))
    except yaml.YAMLError:
        raise LocalError("Unable to parse %s" % path)
    except IOError:
        raise LocalError("Unable to open %s for reading" % path)

def process_environments():
    environment_files = os.listdir(args.environments)
    environment_files = filter(lambda x: re.match(".+?.yaml$", x),
        environment_files)
    environment_files = filter(lambda x: x not in ENVIRONMENTS_BLACKLIST,
        environment_files)
    for environment_file in environment_files:
        logging.info("Processing '%s'..." % environment_file)

        try:
            environment = read_environment_definition(environment_file)
        except LocalError, error:
            logging.error(error)
            continue

        environment['name'] = re.sub(".yaml$", "", environment_file)

        try:
            foreman_environment = get_environment(environment['name'])
            logging.debug("Found Foreman environment '%s'..." %
                foreman_environment['name'])
        except ForemanError, error:
            logging.error("Environment '%s' not found in Foreman" % \
                environment_file)
            continue

        notify(environment, foreman_environment)

def notify(environment, foreman_environment):
    logging.info("Environment '%s' has %d hosts" %
        (environment['name'], foreman_environment['hosts_count']))

    created = dateutil.parser.parse(foreman_environment['created_at'])
    created = created.replace(tzinfo=None)
    threshold = datetime.datetime.now() - datetime.timedelta(days=1)
    if foreman_environment['hosts_count'] == 0 and created < threshold:
        if not args.dryrun:
            send_email_environment_empty(environment['name'],
             environment['notifications'])
        else:
            logging.info("Email not sent because dryrun flag is on")

def main():
    """Application entrypoint"""
    global args
    args = parse_cmdline_args()
    configure_logging()

    try:
        os.stat(args.environments)
        if not os.path.isdir(args.environments):
            raise OSError()
    except OSError:
        logging.error("'%s' is not readable or not a directory. Exiting...")
        return 2

    try:
        verify_kerberos()
    except LocalError, error:
        logging.error("TGT not found or expired. Exiting...")
        return 3

    process_environments()
    return 0

if __name__ == '__main__':
    sys.exit(main())
