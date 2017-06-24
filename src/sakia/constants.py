import os
import yaml

MAX_CONFIRMATIONS = 6

with open(os.path.join(os.path.dirname(__file__), "root_servers.yml"), 'r') as stream:
    ROOT_SERVERS = yaml.load(stream)

with open(os.path.join(os.path.dirname(__file__), "g1_licence.html"), 'r') as stream:
    G1_LICENCE = stream.read()
