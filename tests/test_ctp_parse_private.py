from midomtoolbox.ctp.translation import parse_private_dict
from tests import RESOURCE_PATH


def test_private_parsing():
    private = parse_private_dict(RESOURCE_PATH / "PrivateTagDictionary.xml")

    assert len(private) == 7
    assert len(private[0].elements) == 31
