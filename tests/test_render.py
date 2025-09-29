from tabulate import tabulate

from midomtoolbox.render import (
    render_private_tags_table,
    render_protocol,
    render_tags_table,
    to_tags_table_contents,
)


def test_render_base(a_protocol):

    output = ""
    for sop_class, tags in a_protocol.tags.items():
        output += f"SOPClass '{sop_class}\n'"
        table = to_tags_table_contents(tags)
        output += tabulate(table, headers="keys", tablefmt="rst")

    assert output  # enough for now


def test_render_tags(a_protocol):
    rendered = []
    for sop_class, tags in a_protocol.tags.items():
        rendered.append(f"{sop_class}\n" + render_tags_table(tags))

    assert rendered


def test_render_private_tags(a_protocol):
    output = render_private_tags_table(a_protocol.private)
    assert output


def test_whole_protocol(a_protocol):
    """Combine several templates into one"""
    output = render_protocol(a_protocol)
    assert output
