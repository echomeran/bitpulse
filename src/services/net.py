import os

import certifi
import requests

# Android builds have no system CA store visible to Python; point every TLS client at certifi's bundle.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

session = requests.Session()
session.verify = certifi.where()
session.headers.update({"User-Agent": "Mozilla/5.0 (BitPulse/1.1)"})
