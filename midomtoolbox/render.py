"""Write and export MIDOM protocol files"""
from typing import List

from jinja2 import Environment, PackageLoader
from midom.components import PrivateAllowGroup, Protocol, TagAction

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


def render_protocol(protocol: Protocol):
    """Render tags list to a markup table"""

    # convert tags here as jinja cannot run the TagAction.identifier.key() method..
    protocol.tags = {
        sop_class: to_tags_table_contents(tag_actions)
        for sop_class, tag_actions in protocol.tags.items()
    }
    output = jinja_env.get_template("protocol.md.j2").render(protocol=protocol)
    return output
