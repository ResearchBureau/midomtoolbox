from _pytest.fixtures import fixture

from midomtoolbox.extraction.reader import (
    create_protocol,
    extract_tag_identifiers,
)


@fixture
def input_list():
    return """
Series Description
Study Date
Study Instance UID
Series Instance UID
SOP Instance UID
Series Date
Acquisition Date
Image Date
Study Time
Series Time
Acquisition Time
Image Time
Instance Creation Date
Instance Creation Time
Group Length
File Meta Information Version
Specific Character Set
Modality
Manufacturer
"""


def test_reader(input_list):

    raw = extract_tag_identifiers(input_list)
    parsed = raw.parsed()
    unknown = raw.unknown()

    assert len(raw.lines) == 19
    assert len(parsed) == 16
    assert len(unknown) == 3


def test_create_protocol(input_list):
    protocol = create_protocol(input_list)
    assert len(protocol.tags["*"]) == 16
