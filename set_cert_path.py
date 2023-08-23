import certifi
import os

# set environmnent variable for certifi
os.environ['SSL_CERT_FILE'] = certifi.where()