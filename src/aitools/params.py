import logging

DEFAULT_LOGGING_LEVEL=logging.INFO
CERN_CA_BUNDLE = "/etc/ssl/certs/CERN-bundle.pem"
FQDN_VALIDATION_RE = "^[a-zA-Z0-9][a-zA-Z0-9\-]{0,59}?\.cern\.ch$"
HASHLEN = 10
