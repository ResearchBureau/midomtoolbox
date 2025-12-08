from midomtoolbox.generators import (
    PrivateAllowGroupFactory,
    PrivateBlockTagIdentifierFactory,
    ProtocolFactory,
    RepeatingGroupFactory,
    SingleTagFactory,
    TagActionFactory,
    TagIdentifierFactory,
)


def test_tag_identifier_generators():
    """Just run through them and nothing should crash"""

    tag = SingleTagFactory()
    group = RepeatingGroupFactory()
    private = PrivateBlockTagIdentifierFactory()

    identifiers = [TagIdentifierFactory() for _ in range(20)]

    assert tag
    assert group
    assert private
    assert identifiers


def test_protocol_generators():
    action = TagActionFactory()
    private_group = PrivateAllowGroupFactory()
    protocol = ProtocolFactory()

    assert action
    assert private_group
    assert protocol
