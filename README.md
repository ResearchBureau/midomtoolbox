# MIDOM Toolbox

[![CI](https://github.com/ResearchBureau/midomtoolbox/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/ResearchBureau/midomtoolbox/actions/workflows/build.yml?query=branch%3Amain)
[![PyPI](https://img.shields.io/pypi/v/midomtoolbox)](https://pypi.org/project/midomtoolbox/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/midomtoolbox)](https://pypi.org/project/midomtoolbox/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

Shape, convert, summarize and analyse MIDOM deidentification Protocols. 

_⚠️ Major version 0. Not feature complete. Still testing out the interface_

* Works with MIDOM Protocols (https://pypi.org/project/midom/)
* Converts to CTP scripts
* Generates summaries

## installation
```
pip install midomtoolbox
```

## usage

### Working with Protocols
To take a MIDOM protocol json file and render to markup format:
```python
from midom.components import Protocol    
from midomtoolbox.render.markdown import render_protocol

# load protocol
with open("/tmp/ctp_pipeline.json") as f:
    protocol = Protocol.model_validate_json(f.read())

# render
with open("/tmp/output.md", "w") as f:
    f.write(render_protocol(protocol))
```

### Validation
TODO

### Other examples
See [/examples](https://github.com/ResearchBureau/midomtoolbox/tree/main/examples) 

## FAQ
**Why MIDOM and MIDOMToolbox? Why not just all MIDOM?**
MIDOM is about an Object Model; it is as implementation-agnostic as possible. It has
some python implementations for convenience, for JSON serialization for example. But 
the value is mostly in the interfaces it describes. It should be light-weight to
include in other python packages, keeping its own package dependencies minimal


MIDOMToolbox is a library that fully embraces python and provides tools for anything
involving MIDOM objects. As a toolbox, it is free to have a large number of dependencies.