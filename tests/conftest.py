import os

import pytest
from midom.components import (
    CriterionString,
    Filter,
    PixelArea,
    PixelOperation,
    PrivateAllowGroup,
    PrivateElement,
    Protocol,
    TagAction,
)
from midom.constants import ActionCodes
from midom.identifiers import (
    PrivateAttributes,
    PrivateBlockTagIdentifier,
    RepeatingGroup,
    SingleTag,
)


@pytest.fixture
def a_protocol():
    return Protocol(
        tags={
            "1.2.840.10008.5.1.4.1.1.2": [
                TagAction(
                    identifier=SingleTag("PatientID"),
                    action=ActionCodes.REMOVE,
                    justification="",
                ),
                TagAction(
                    identifier=SingleTag("Modality"),
                    action=ActionCodes.KEEP,
                    justification="",
                ),
                TagAction(
                    identifier=PrivateAttributes(),
                    action=ActionCodes.REMOVE,
                    justification="",
                ),
                TagAction(
                    identifier=PrivateBlockTagIdentifier("112d['company']3f"),
                    action=ActionCodes.KEEP,
                    justification="",
                ),
                TagAction(
                    identifier=RepeatingGroup("50xx,xxxx"),
                    action=ActionCodes.DUMMY,
                    justification="",
                ),
                TagAction(
                    identifier=SingleTag(0x3313001D),
                    action=ActionCodes.KEEP,
                    justification="",
                ),  # unknown tag
            ],
            "1.2.840.10008*": [
                TagAction(
                    identifier=SingleTag("PatientID"),
                    action=ActionCodes.REMOVE,
                    justification="",
                ),
                TagAction(
                    identifier=SingleTag("Modality"),
                    action=ActionCodes.REMOVE,
                    justification="",
                ),
                TagAction(
                    identifier=PrivateAttributes(),
                    action=ActionCodes.REMOVE,
                    justification="",
                ),
            ],
        },
        filters=[
            Filter(
                criterion=CriterionString(
                    content="Modality.equals('US') and BurntInAnnotation.equals('No')"
                ),
                justification="important",
            ),
            Filter(
                criterion=CriterionString(
                    content="SOPClassUID.equals('123456')"
                ),
                justification="this sopclass is bad",
            ),
        ],
        pixel=[
            PixelOperation(
                description="Model this and that",
                criterion=CriterionString(
                    content="Rows.equals(1024) and Columns.equals(720) and "
                    "Modelname.equals('Company bla')"
                ),
                areas=[PixelArea(area=(0, 0, 720, 50))],
            ),
            PixelOperation(
                description="Another test operation",
                criterion=CriterionString(
                    content="Rows.equals(1024) and Columns.equals(740) and "
                    "Modelname.equals('Canon bla')"
                ),
                areas=[PixelArea(area=(0, 0, 720, 150))],
            ),
        ],
        private=[
            PrivateAllowGroup(
                justification="Is really safe. See https://a_link_to_dicom_"
                "conformance_statement",
                elements=[
                    PrivateElement(
                        identifier='0075["company"]01',
                        description="Amount of contrast used",
                        value_representation="LO",
                    ),
                    PrivateElement(
                        identifier='0075["company"]02',
                        description="algorithm settings",
                        value_representation="LO",
                        value_multiplicity="2",
                    ),
                ],
            ),
            PrivateAllowGroup(
                justification="Allowed by our department",
                elements=[
                    PrivateElement(
                        identifier='0011["different"]01',
                        description="Amount of contrast used",
                        value_representation="LO",
                    ),
                    PrivateElement(
                        identifier='0075["different"]04',
                        description="algorithm settings",
                        value_representation="LO",
                        value_multiplicity="4",
                    ),
                    PrivateElement(
                        identifier='0075["different"]05',
                        description="something else",
                        value_representation="OB",
                        value_multiplicity="1",
                    ),
                ],
            ),
        ],
    )


class TestResourcesFolder:
    def __init__(self, calling_file_path, relative_folder=""):
        r"""A folder containing test resources.

        In my python project folders I usually have a /tests/test_resources folder
        that contains files and folders used by tests. This class makes getting
        files from there easier. I don't want to be bothered with a lot of calls
        to os.path.abspath(os.path.join(os.path.dirname)).

        Parameters
        ----------
        calling_file_path: str
            full path of the file calling this function. Typically, you would put
             __file__ as input here
        relative_folder: str
            Relative path to the test resources folder. This folder is assumed to
            be in the same folder as the calling
            file

        Examples
        --------
        # if called from a file \\code\\myproject\run.py:
        >>> test_resources_folder = TestResourcesFolder(__file__,
                                    "tests/test_resources")
        >>> test_resources_folder.base_path
        \\code\\myproject\tests\test_resources

        >>> test_resources_folder.get_path("test1\file1.dcm")
        \\code\\myproject\tests\test_resources\test1\file1.dcm

        """

        calling_file_folder = os.path.dirname(
            os.path.realpath(calling_file_path)
        )
        self.base_path = os.path.join(calling_file_folder, relative_folder)

    def get_path(self, relative_path):
        """Get full path to relative to base path

        Parameters
        ----------
        relative path: str
            path to dir of file relative to base path

        Raises
        ------
        FileNotFoundError:
            if requested path does not exist

        """
        path = os.path.join(self.base_path, relative_path)
        if not os.path.exists(path):
            msg = f"Testfile '{path}' does not exist"
            raise FileNotFoundError(msg)
        return path
