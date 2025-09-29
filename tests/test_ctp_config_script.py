import unittest

from pydicom import DataElement, Dataset

from midomtoolbox.ctp.config_script import CTPConfigScriptFile
from midomtoolbox.ctp.elements import CTPConfigScriptContext
from tests.conftest import TestResourcesFolder


class DicomFileTester(unittest.TestCase):
    def setUp(self):
        self.test_resources_folder = TestResourcesFolder(
            __file__, r"test_resources"
        )

    def test_parse_single_file(self):
        """Read in a single CTP cconfig file and try to parse it and then resolve it
        using some values
        """
        dicom_values = Dataset()
        elem = DataElement(
            0x00750010, "LT", "ANONYMIZER"
        )  # Private creator tag
        dicom_values.add(elem)
        elem = DataElement(0x00751079, "LO", "YES")
        dicom_values.add(elem)

        script_file = self.test_resources_folder.get_path(
            "CTP_scripts/finalCompanyScriptFullDates.script"
        )

        parser = CTPConfigScriptFile(script_file)
        script = parser.parse()
        self.assertEqual(len(script.parameters), 2)
        self.assertEqual(len(script.dicom_tag_actions), 284)
        self.assertEqual(len(script.keep), 1)
        self.assertEqual(len(script.remove), 4)

        context = CTPConfigScriptContext(
            parameters=script.parameters, dicom_values=dicom_values
        )
        resolved_script = script.resolve(context)
        self.assertEqual(len(resolved_script.elements), 291)

    def test_parse_single_file_with_skip(self):
        """@skip() is different then other commands; after reading it disregard any
        other directives
        """

        # this script contains only 3 elements, the first being a rule to @skip()
        # under certain conditions
        script_file = self.test_resources_folder.get_path(
            "CTP_scripts/DicomAnonymizerRemoveAllPrivateTags.script"
        )

        parser = CTPConfigScriptFile(script_file)
        script = parser.parse()
        # the original script should have 3 elements
        self.assertEqual(len(script.elements), 3)

        # Some context that should trigger the @skip()
        dicom_values = Dataset()
        elem = DataElement(
            0x00750010, "LT", "ANONYMIZER"
        )  # Private creator tag
        dicom_values.add(elem)
        elem = DataElement(0x00751080, "LO", "YES")
        dicom_values.add(elem)
        context = CTPConfigScriptContext(
            parameters=script.parameters, dicom_values=dicom_values
        )

        # now resolve the script to its final form
        resolved_script = script.resolve(context)

        # the first element was @skip(). This means that element and any
        # subsequent elements should no longer be present in the script
        self.assertEqual(len(resolved_script.elements), 0)

        # but now, use different context, that does NOT trigger the skip.
        dicom_values = Dataset()
        elem = DataElement(
            0x00750010, "LT", "ANONYMIZER"
        )  # Private creator tag
        dicom_values.add(elem)
        elem = DataElement(0x00751080, "LO", "NO")
        dicom_values.add(elem)
        context = CTPConfigScriptContext(
            parameters=script.parameters, dicom_values=dicom_values
        )

        # The script should still have all of its elements
        resolved_script = script.resolve(context)
        self.assertEqual(len(resolved_script.elements), 3)

    def test_parse_single_rule(self):
        """Focus on dealing with a single @if rule and see whether it resolves
        correctly
        """
        dicom_values = Dataset()
        elem = DataElement(
            0x00750010, "LT", "ANONYMIZER"
        )  # Private creator tag
        dicom_values.add(elem)
        elem = DataElement(0x00751077, "LO", "YES")
        dicom_values.add(elem)

        script_file = self.test_resources_folder.get_path(
            "CTP_scripts/finalCompanyScriptFullDates.script"
        )
        script_file = CTPConfigScriptFile(script_file)
        script = script_file.parse()

        # try a real rule, with substitution and everything
        single_action = script.dicom_tag_actions[
            73
        ]  # rule to keep or remove PatientAge
        context = CTPConfigScriptContext(
            parameters=script.parameters, dicom_values=dicom_values
        )
        single_action.resolve(context)
        self.assertEqual(
            single_action.ctp_script_string(),
            '<e en="T" t="00101010" n="PatientAge">@keep()</e>',
        )

        # try flat rule, with just one command
        single_action = script.dicom_tag_actions[
            26
        ]  # rule to keep or remove PatientAge
        single_action.resolve(context)
        self.assertEqual(
            single_action.ctp_script_string(),
            '<e en="T" t="00080090" n="ReferringPhysicianName">@empty()</e>',
        )
