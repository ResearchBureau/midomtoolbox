"""How to convert existing CTP scripts to a MIDOM protocol"""
from pathlib import Path
from typing import List

from midom.components import Filter, PixelOperation, Protocol

from midomtoolbox.ctp.config_script import load_script_file
from midomtoolbox.ctp.translation import parse_private_dict, to_tag_actions

# Load a CPT tag action script (what to do with which DICOM tag)
ctp_script = load_script_file(Path("ctp_tags_example.script"))
tag_actions = to_tag_actions(ctp_script.dicom_tag_actions)

# Load all CTP filters
# Convert these to MIDOM protocol filter elements
filters: List[Filter] = []  # TODO: write filter conversion

# Load CTP pixeldata script
# Convert to MIDOM protocol pixel elements
pixel: List[PixelOperation] = []  # TODO: write pixel conversion

# Load CTP private tag collection and convert these to MIDOM protocol safe private
# group definition
private = parse_private_dict("./cpt_private_dict_example.xml")


# Put this all together into a single MIDOM protocol object
protocol = Protocol(
    tags={"*": tag_actions},  # dict per SOPClass, all SOPClasses here
    filters=filters,
    pixel=pixel,
    private=private,
)


# Save to disk
output_file = "/tmp/converted_from_ctp.json"
with open(output_file, "w") as f:
    f.write(protocol.model_dump_json(indent=2))
    print(f"Done. Wrote to {output_file}")
