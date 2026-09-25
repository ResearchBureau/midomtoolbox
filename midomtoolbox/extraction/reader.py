"""Functions for quickly generating an approximate protocol that can serve as a basis
for further tweaking
"""
from typing import Iterable, List, Optional, Tuple

from midom.components import Protocol, TagAction
from midom.constants import ActionCode, ActionCodes
from midom.identifiers import TagIdentifier, tag_identifier_from_string

from midomtoolbox.extraction.matcher import find_dicom_keyword
from midomtoolbox.logs import get_module_logger

logger = get_module_logger("reader")


class ParseError(Exception):
    pass


class RawProtocol:
    """Intermediate stage for parsing free text lines"""

    def __init__(self, lines: List[Tuple[str, Optional[TagIdentifier]]]):
        self.lines = lines

    def parsed(self) -> List[TagIdentifier]:
        return [y for x, y in self.lines if y is not None]

    def unknown(self) -> List[str]:
        return [x for x, y in self.lines if x and y is None]


def extract_tag_identifiers(input_text) -> RawProtocol:
    """Try to parse out a MIDOM protocol tag identifiers from semi-structured text

    Returns
    -------
    List[Tuple[str,TagIdentifier]]
        Each line in input with either a Tag

    """
    output = []
    for line in [x for x in input_text.split("\n") if not x == ""]:
        try:
            output.append((line, create_tag_identifier(line)))
        except ParseError:
            output.append((line, None))

    return RawProtocol(lines=output)


def create_tag_identifier(string_in):
    """Try to create a MIDOM TagIdentifier matching input string
    Raises
    ------
    ParseError
        If string_in cannot be matched to any TagIdentifier
    """
    keyword = find_dicom_keyword(string_in)
    if not keyword:
        raise ParseError(
            f'Could not match "{string_in}" to any known DICOM element'
        )
    try:
        return tag_identifier_from_string(keyword)
    except ValueError as e:
        raise ParseError(
            f'Could not match "{string_in}" to any ' f"known tag identifier"
        ) from e


def create_tag_actions(
    identifiers: Iterable[TagIdentifier], actioncode: ActionCode
) -> List[TagAction]:
    """Create a MIDOM TagAction (what to do with a dicom tag) for each identifier,
    using given actioncode
    """
    return [
        TagAction(action=actioncode, identifier=x, justification="")
        for x in identifiers
    ]


def create_protocol(tags_to_remove=None, tags_to_keep=None):
    actions = []

    if tags_to_remove:
        raw = extract_tag_identifiers(tags_to_remove)
        actions = actions + create_tag_actions(
            raw.parsed(), actioncode=ActionCodes.REMOVE
        )
        if raw.unknown():
            logger.warning(f"Could not find match for {raw.unknown()}")

    if tags_to_keep:
        raw = extract_tag_identifiers(tags_to_keep)
        actions = actions + create_tag_actions(
            raw.parsed(), actioncode=ActionCodes.KEEP
        )
        if raw.unknown():
            logger.warning(f"Could not find match for {raw.unknown()}")

    return Protocol(tags={"*": actions})
