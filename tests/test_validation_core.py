import pytest

from midomtoolbox.comparison.core import NamedProtocol, compare
from midomtoolbox.generators import ProtocolFactory


def test_comparison():
    """Basic comparison of two protocols

    Mainly check for non-crash
    """

    protocol_one = NamedProtocol(
        name="Protocol One (tm)", protocol=ProtocolFactory.build()
    )
    the_other_one = NamedProtocol(
        name="Different Protocol", protocol=ProtocolFactory.build()
    )

    with pytest.raises(ValueError):
        # comparison can only be done if the SOPClasses are the same. Random
        # SOPClasses are not the same (unless you generated identical ones in which
        # case congrats.
        compare(protocol_one, the_other_one)

    # make SOPClass names the same
    protocol_one.protocol.tags = {
        "*": list(protocol_one.protocol.tags.values())[0]
    }
    the_other_one.protocol.tags = {
        "*": list(the_other_one.protocol.tags.values())[0]
    }

    compare(protocol_one, the_other_one)
