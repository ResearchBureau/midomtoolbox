from dataclasses import dataclass
from itertools import chain
from typing import List, Optional

from midom.components import Protocol, TagAction
from midom.constants import ActionCodes
from midom.identifiers import TagIdentifier


class NamedProtocol:
    """A MIDOM protocol with a name. For better printing"""

    def __init__(self, name: str, protocol: Protocol):
        self.name = name
        self.protocol = protocol

    def sop_class_uids(self):
        return self.protocol.tags.keys()

    def get_tags(self, sop_class: str):
        return self.protocol.tags[sop_class]

    def __str__(self):
        return self.name


@dataclass
class ProtocolAction:
    """MIDOM TagAction linked to NamedProtocol. For printing comparisons.
    Tag_action can be None, meaning no action is defined
    """

    tag_action: Optional[TagAction]
    protocol: NamedProtocol

    def tag_action_string(self):
        if self.tag_action is None:
            return "None"
        else:
            return self.tag_action.action.var_name

    def __str__(self):

        return f"{self.protocol} - {self.tag_action_string()}"


def get_strictness(protocol_action: ProtocolAction):
    """How strict is this action at constraining information? From keep (Not strict)
    to Remove the element (very strict)

    Groups actions by their effects:
    * Do nothing (Keep, None)
    * Change value to have less information (UID, CLEAN)
    * Make value inaccessible (dummy, empty)
    * Remove value and all traces (remove)

    Considers certain action to have the same strictness if the effect is similar.
    For instance, DUMMY and UID both fill any value, effectively obfuscating the
    value.

    """
    if protocol_action.tag_action is None:
        action = None
    else:
        action = protocol_action.tag_action.action

    strictness = {
        None: 0,
        ActionCodes.KEEP: 0,
        ActionCodes.CLEAN: 1,
        ActionCodes.UID: 1,
        ActionCodes.DUMMY: 2,
        ActionCodes.EMPTY: 2,
        ActionCodes.EMPTY_OR_DUMMY: 2,
        ActionCodes.REMOVE_OR_DUMMY: 2,
        ActionCodes.REMOVE_OR_EMPTY: 2,
        ActionCodes.REMOVE_OR_EMPTY_OR_DUMMY: 2,
        ActionCodes.REMOVE_OR_EMPTY_OR_UID: 2,
        ActionCodes.REMOVE: 3,
    }

    return strictness[action]


@dataclass
class ActionPair:
    """Two ProtocolActions for a single identifier"""

    identifier: TagIdentifier
    action_a: ProtocolAction
    action_b: ProtocolAction

    @property
    def identifier_name(self):
        return self.identifier.name()


def extract_tags(np: NamedProtocol, sop_class: str) -> List[ProtocolAction]:
    """Collect and tag tags for two protocols"""
    return [ProtocolAction(x, np) for x in np.get_tags(sop_class)]


def compare(a: NamedProtocol, b: NamedProtocol):
    # compare tags
    # per SOPClassUID
    if a.sop_class_uids() != b.sop_class_uids():
        raise ValueError(
            f"Protocol {a} and {b} have differing SOPClassUIDs. {a.sop_class_uids()} "
            f"vs {b.sop_class_uids()} If you want this functionality please "
            f"implement it"
        )

    for sop_class in a.sop_class_uids():
        actions_a = {x.identifier: x for x in a.get_tags(sop_class)}
        actions_b = {x.identifier: x for x in b.get_tags(sop_class)}

        all_keys = {
            x.identifier
            for x in chain(a.get_tags(sop_class), b.get_tags(sop_class))
        }

        # make sure that a value exists for any tags mentioned in either protocol
        # If no action is defined, add None (trough .get(x))
        all_actions = [
            ActionPair(
                identifier=x,
                action_a=ProtocolAction(actions_a.get(x), a),
                action_b=ProtocolAction(actions_b.get(x), b),
            )
            for x in all_keys
        ]

        stricter_in_a = [
            x
            for x in all_actions
            if get_strictness(x.action_a) > get_strictness(x.action_b)
        ]
        stricter_in_b = [
            x
            for x in all_actions
            if get_strictness(x.action_a) < get_strictness(x.action_b)
        ]
        equal_in_a_b = [
            x
            for x in all_actions
            if get_strictness(x.action_a) == get_strictness(x.action_b)
        ]

        stricter_in_a.sort(key=lambda x: x.identifier, reverse=True)
        stricter_in_b.sort(key=lambda x: x.identifier, reverse=True)
        equal_in_a_b.sort(key=lambda x: x.identifier, reverse=True)

        print_action_list(stricter_in_a, f"Stricter in {a.name}")
        print_action_list(stricter_in_b, f"Stricter in {b.name}")
        print_action_list(equal_in_a_b, f"Equal in {a.name} and {b.name}")


def print_action_list(pairs: List[ActionPair], title: str):
    print(f"* {title}")
    for action_pair in pairs:
        print(
            f"{action_pair.identifier}, {action_pair.identifier_name}, "
            f"{action_pair.action_a}, {action_pair.action_b}"
        )

    print("\n")
