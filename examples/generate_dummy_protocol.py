"""Generate a protocol with random values"""
from midomtoolbox.generators import ProtocolFactory
from midomtoolbox.render.markdown import render_protocol

protocol = ProtocolFactory.build()
protocol.sort_tags()  # Sort from specific to general


out_file = "/tmp/output.md"
with open(out_file, "w") as f:
    print(f"wrote to {out_file}")
    f.write(render_protocol(protocol))
