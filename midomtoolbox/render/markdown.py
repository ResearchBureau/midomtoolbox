"""Writing MIDOM protocol files as markup files"""
from typing import Dict, List

from jinja2 import Environment, PackageLoader
from midom.components import (
    Filter,
    PixelOperation,
    PrivateAllowGroup,
    Protocol,
    TagAction,
)
from pydantic import BaseModel
from pydicom.uid import UID

jinja_env = Environment(loader=PackageLoader("midomtoolbox", "templates"))


def to_tags_table_contents(tag_actions: List[TagAction]):
    """Extract printable information from a tag list. Pre-processing step."""
    output = []
    for tag_action in tag_actions:
        output.append(
            {
                "identifier": str(tag_action.identifier),
                "name": tag_action.identifier.key(),
                "action": tag_action.action.var_name,
                "comment": tag_action.justification,
            }
        )
    return output


def render_tags_table(actions=List[TagAction]):
    """Render tags list to a markup table"""
    tags_table = to_tags_table_contents(actions)
    output = jinja_env.get_template("tags_table.md.j2").render(
        tags_table=tags_table
    )
    return output


def render_private_tags_table(private=List[PrivateAllowGroup]):
    """Render tags list to a markup table"""

    output = jinja_env.get_template("private_tags_table.md.j2").render(
        private=private
    )
    return output


class ProtocolContents(BaseModel):
    """Contains all contents that should be sent to jinja.

    Separated this from Protocol itself to be free to alter internals, rewrite text
    etc., just for rendering purposes. I don't want to pass along a Protocol instance
    that actually is not a Protocol any more.
    """

    tags: Dict[str, List[TagAction]]
    filters: List[Filter]
    pixel: List[PixelOperation]
    private: List[PrivateAllowGroup]

    @classmethod
    def init_from_protocol(cls, protocol_in):
        return cls(
            tags=protocol_in.tags,
            filters=protocol_in.filters,
            pixel=protocol_in.pixel,
            private=protocol_in.private,
        )


def render_protocol(protocol: Protocol):
    """Render tags list to a markup table"""

    # convert tags here as jinja cannot run the TagAction.identifier.key() method..
    pc = ProtocolContents.init_from_protocol(protocol)
    pc.tags = {
        f"{UID(sop_class).name} ({sop_class})": to_tags_table_contents(
            tag_actions
        )
        for sop_class, tag_actions in pc.tags.items()
    }
    output = jinja_env.get_template("protocol.md.j2").render(
        protocol_contents=pc
    )
    return output
