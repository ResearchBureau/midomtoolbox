"""Generators for MIDOM objects. For testing and dummy creation."""
from collections import OrderedDict
from typing import List

import factory
from factory import fuzzy
from faker import Faker
from midom.components import (
    CriterionString,
    Filter,
    PixelOperation,
    PrivateAllowGroup,
    PrivateElement,
    Protocol,
    TagAction,
)
from midom.constants import ActionCodes
from midom.identifiers import (
    AnyAttribute,
    PrivateAttributes,
    PrivateBlockTagIdentifier,
    RepeatingGroup,
    SingleTag,
)
from pydicom._uid_dict import UID_dictionary
from pydicom.datadict import DicomDictionary
from pydicom.valuerep import VR


class SingleTagFactory(factory.Factory):
    """Identifies one or more DICOm tags"""

    class Meta:
        model = SingleTag

    # use any dicom tag by default
    tag = fuzzy.FuzzyChoice([x[4] for x in DicomDictionary.values()])


class RepeatingGroupFactory(factory.Factory):
    """Identifies one or more DICOm tags"""

    class Meta:
        model = RepeatingGroup

    @factory.lazy_attribute
    def tag(self):
        return f"{factory.random.randgen.randint(1, 255):02x}xx, xxxx"


def elements_to_private_string(group: int, private_creator: str, element: int):
    """Generate a string like 0013,[some_creator]01 from its separate elements
    <group>,[<private_creator>]<element>
    """
    return f"{group :04x}, [{private_creator}]{element:02x}"


UNSET = object()  # unique object for use below


class PrivateBlockTagIdentifierFactory(factory.Factory):
    """Creates a private tag identifier

    Explanation of somewhat cryptic setup with Params and seemingly invalid
    references to self.group self.element:

    This is to make it possible to instantiate this factory with both a full
    string like

    PrivateBlockTagIdentifierFactory('0011,[creator]01')

    But also allow easy creation of related entries with repeated calls
    PrivateBlockTagIdentifierFactory(group=0x0011, private_creator='creator')

    '0011,[creator]01'
    '0011,[creator]02'
    '0011,[creator]03'

    For Factory Boy Params, see
    https://factoryboy.readthedocs.io/en/stable/reference.html#parameters
    """

    class Meta:
        model = PrivateBlockTagIdentifier

    class Params:
        group = UNSET
        element = UNSET
        private_creator = UNSET

    @factory.lazy_attribute
    def tag(self):
        group = self.group
        element = self.element
        private_creator = self.private_creator

        # set random values values if not set
        if group == UNSET:
            group = factory.random.randgen.randint(0, 32639) * 2 + 1
        if element == UNSET:
            element = factory.random.randgen.randint(1, 255)
        if private_creator == UNSET:
            private_creator = (
                Faker().sentence(nb_words=3).replace(" ", "_").replace(".", "")
            )

        return f"{group :04x}, [{private_creator}]{element:02x}"


class TagIdentifierFactory(factory.Factory):
    """TagIdentifier is an abstract base class. Re-direct to a random child class.

    Does not include Private Block tags, as these are often treated separately
    """

    class Meta:
        model = (
            lambda: None
        )  # noqa: E731  - We'll override the actual creation

    # all possible TagIdentifier Child classes, with weight factor

    CHILD_CLASSES = OrderedDict(
        [
            (PrivateAttributes, 0.001),
            (AnyAttribute, 0.009),
            (SingleTagFactory, 0.8),
            (RepeatingGroupFactory, 0.19),
        ]
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Randomly choose one of the factories
        child = Faker().random_elements(
            cls.CHILD_CLASSES, length=1, use_weighting=True
        )[0]
        if isinstance(child, factory.Factory):
            return child.create(**kwargs)
        else:
            return child()

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        child = Faker().random_element(cls.CHILD_CLASSES)
        if isinstance(child, factory.Factory):
            return child.build(**kwargs)
        else:
            return child()


class TagActionFactory(factory.Factory):
    class Meta:
        model = TagAction

    identifier = factory.SubFactory(TagIdentifierFactory)
    action = factory.fuzzy.FuzzyChoice(ActionCodes.ALL)
    justification = "A Justification"


class PrivateElementFactory(factory.Factory):
    class Meta:
        model = PrivateElement

    identifier = factory.SubFactory(PrivateBlockTagIdentifierFactory)
    description = factory.Sequence(lambda x: f"PrivateElement_{x}")
    value_representation = factory.fuzzy.FuzzyChoice(VR)
    value_multiplicity = "1"


def generate_action_list(length=10):
    """A random list of tag actions"""
    return sorted(
        list(TagActionFactory() for _ in range(length)),
        key=lambda x: x.identifier.number_of_matchable_tags(),
    )


def pick_sop_classes(number):
    """A number of valid SOPClassUID without duplicates"""
    return Faker().random_elements(UID_dictionary.keys(), length=number)


def generate_tags_list_item():
    """A single SOPClassUID with associated action list"""
    return {x: generate_action_list(length=20) for x in pick_sop_classes(3)}


def generate_private_tags(length=15):
    """Generate a list of PrivateElements with identical group number and
    private creator
    """
    first = PrivateBlockTagIdentifierFactory()
    rest = [
        PrivateBlockTagIdentifierFactory(
            group=first.group, private_creator=first.private_creator
        )
        for _ in range(length)
    ]
    return [PrivateElementFactory(identifier=x) for x in rest]


class PrivateAllowGroupFactory(factory.Factory):
    class Meta:
        model = PrivateAllowGroup

    elements = factory.LazyFunction(generate_private_tags)
    justification = factory.LazyFunction(
        lambda: "A Justification for why these tags are "
        f"safe: '{Faker().sentence(nb_words=10)}'"
    )


class CriterionStringFactory(factory.Factory):
    class Meta:
        model = CriterionString

    content = (
        "SOPClassUID.equals('1.2.840.10008.5.1.4.1.1.11.1') and"
        " not SeriesDescription.equals('Annotation')"
    )


class FilterFactory(factory.Factory):
    class Meta:
        model = Filter

    criterion = factory.SubFactory(CriterionStringFactory)
    justification = factory.LazyFunction(
        lambda: f"Reject some datasets because of: {Faker().sentence(nb_words=5)}'"
    )


class ProtocolFactory(factory.Factory):
    class Meta:
        model = Protocol

    tags = factory.LazyFunction(generate_tags_list_item)
    filters: List[Filter] = factory.List(
        [factory.SubFactory(FilterFactory) for _ in range(3)]
    )
    pixel: List[PixelOperation] = []
    private = factory.List(
        [factory.SubFactory(PrivateAllowGroupFactory) for _ in range(4)]
    )
