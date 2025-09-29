"""Functions and Classes for Translating CTP objects to MIDOM and DICOM objects"""
from collections import defaultdict
from typing import List

from midom.components import PrivateAllowGroup, PrivateElement, TagAction
from midom.constants import ActionCodes
from midom.identifiers import tag_identifier_from_string

from midomtoolbox.ctp.config_script import CTPTraceableTagAction
from midomtoolbox.ctp.elements import CTPRule
from midomtoolbox.ctp.exceptions import (
    CTPScriptParseError,
    CTPScriptProcessIsNoActionError,
)
from midomtoolbox.ctp.tagdictionary import TagDictionaryFile


def to_action_code(ctp_action_name: str):
    """Which CTP commands correspond to which ActionCodes?"""
    if ctp_action_name == "keep":
        return ActionCodes.KEEP
    elif ctp_action_name.startswith("hashuid"):
        return ActionCodes.UID
    elif ctp_action_name == "remove":
        return ActionCodes.REMOVE
    elif ctp_action_name == "empty":
        return ActionCodes.EMPTY
    elif ctp_action_name.startswith("hash"):
        return ActionCodes.DUMMY
    elif ctp_action_name.startswith("date"):  # date() writes the current date
        return ActionCodes.DUMMY
    elif ctp_action_name == "contents":
        return ActionCodes.DUMMY
    elif ctp_action_name.startswith("process"):
        raise CTPScriptProcessIsNoActionError(
            "Process() is a CTP-only action, not a DICOM action code"
        )
    else:
        raise CTPScriptParseError(f'Unknown action code "{ctp_action_name}"')


def rule_to_action_code(ctp_rule: CTPRule) -> TagAction:
    """Convert a CTP-parsed rule into a MIDOM TagAction. The CTP rule is not
    guaranteed to contain a single tag action conversion will raise an exception
    in this case.

    Notes
    -----
    The main CTP parsing code is years old and badly written. This new code will
    not attempt to fix, rather to pragmatically get the output out. Apologies.
    """
    if len(ctp_rule.line_elements) > 1:

        rule_str = ctp_rule.ctp_script_string()
        if "always" in rule_str and any(
            x in rule_str
            for x in ("YES", "PerDICOMPS315AnnexEDetailsin00120064")
        ):
            return ActionCodes.DUMMY
        elif "always" in rule_str and any(
            x in rule_str for x in ("UNMODIFIED")
        ):
            return ActionCodes.KEEP
        else:
            raise CTPScriptParseError(
                f"Cannot find action code. CTP rule '{ctp_rule}' "
                f"contains multiple elements '{ctp_rule.line_elements}'"
            )

    ctp_function = ctp_rule.line_elements[0]
    try:
        # if the rule was resolved, use the resolved value
        # (ignoring reasonable mypy objections because this is legacy code. Sorry)
        function_name = ctp_function.resolved_value.name  # type: ignore[attr-defined]
    except AttributeError:
        # otherwise try the rule itself.
        function_name = ctp_function.name  # type: ignore[attr-defined]
    return to_action_code(function_name)


def to_tag_action(ctp_tag_action: CTPTraceableTagAction) -> TagAction:
    """Convert a CTP-parsed action into a MIDOM TagAction"""
    identifier = tag_identifier_from_string(ctp_tag_action.tag_code)

    if (
        ctp_tag_action.tag_code == "00120064"
    ):  # 'DeIdentificationMethodCodeSequence'
        return TagAction(
            identifier=identifier,
            action=ActionCodes.DUMMY,
            justification="Read from CTP",
        )

    return TagAction(
        identifier=identifier,
        action=rule_to_action_code(ctp_tag_action.rule),
        justification="Read from CTP",
    )


def to_tag_actions(ctp_tag_actions):
    """Translate all CTP tag actions to MIDOM TagAction, ignore untranslatable"""
    converted = []
    for ctp_tag_action in ctp_tag_actions:
        try:
            converted.append(to_tag_action(ctp_tag_action))
        except CTPScriptProcessIsNoActionError:
            continue

    return converted


def parse_private_dict(file_path) -> List[PrivateAllowGroup]:
    """Parse a CTP private dictionary file to a MIDOM object

    This will ignore any comments in the CTP file as they are not XML parsable.
    """

    dict_file = TagDictionaryFile(path=file_path)
    parsed = dict_file.parse()
    midom_parsed = [
        PrivateElement(
            identifier=tag_identifier_from_string(x.tag.tag_string),
            description=x.tag_key,
            value_representation=x.VR,
            value_multiplicity=x.VM,
        )
        for x in parsed.elements
    ]
    # separate per privatecreator
    per_creator = defaultdict(list)
    for x in midom_parsed:
        per_creator[x.identifier.private_creator].append(x)
    # sort as hex

    midom_private = []
    for _, private_elements in per_creator.items():
        midom_private.append(
            PrivateAllowGroup(
                elements=sorted(
                    private_elements, key=lambda x: x.identifier.tag
                ),
                justification="Based on CTP script",
            )
        )

    return midom_private
