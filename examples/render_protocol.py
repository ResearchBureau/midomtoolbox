"""Write a MIDOM protocol json as a slightly more readable Markup file"""

from midom.components import Protocol

from midomtoolbox.render import render_protocol

# load protocol
with open("/tmp/ctp_pipeline.json") as f:
    protocol = Protocol.model_validate_json(f.read())

# render
with open("/tmp/output.md", "w") as f:
    f.write(render_protocol(protocol))
