"""Generate a protocol with random values"""
from midomtoolbox.generators import ProtocolFactory

protocol = ProtocolFactory.build()
protocol.sort_tags()  # Sort from specific to general


out_file = "/tmp/protocol.json"
with open(out_file, "w") as f:
    print(f"wrote to {out_file}")
    f.write(protocol.model_dump_json(indent=2))
