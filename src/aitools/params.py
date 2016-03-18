import logging

DEFAULT_LOGGING_LEVEL=logging.INFO
CERN_CA_BUNDLE = "/etc/ssl/certs/CERN-bundle.pem"
FQDN_VALIDATION_RE = "^[a-zA-Z0-9][a-zA-Z0-9\-]{0,62}?(\.[a-zA-Z0-9]{1,63})*\.cern\.ch$"
MAX_FQDN_LEN = 253
HASHLEN = 10
