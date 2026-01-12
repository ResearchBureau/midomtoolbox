from midom.components import Protocol

protocol_path = (
    "/home/sjoerd/code/python/DPS-register/Internal_4/Internal_4.json"
)

with open(protocol_path) as f:
    protocol = Protocol.model_validate_json(f.read())
