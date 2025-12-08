"""Generate a protocol with random values"""
from midomtoolbox.generators import ProtocolFactory
from midomtoolbox.render import render_protocol


protocol = ProtocolFactory.build()

with open("/tmp/output.md", "w") as f:
    f.write(render_protocol(protocol))
