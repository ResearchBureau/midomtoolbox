import unittest
from pathlib import Path

from pydicom import DataElement, Dataset
from pydicom.datadict import DicomDictionary

from midomtoolbox.ctp.config_script import load_script_file
from midomtoolbox.ctp.pipeline import CTPPipeline, PipelineContext
from tests.conftest import TestResourcesFolder


class DicomFileTester(unittest.TestCase):
    def setUp(self):
        self.test_resources_folder = TestResourcesFolder(
            __file__, r"test_resources"
        )

    def test_parse_pipeline_and_summary(self):
        # Load the stages
        test_resources = (
            Path(self.test_resources_folder.base_path) / "CTP_scripts"
        )
        stages = [
            load_script_file(
                test_resources / "finalCompanyScriptpatientNameIdPrefix.script"
            ),
            load_script_file(
                test_resources / "finalCompanyScriptpatientNameIdGiven.script"
            ),
            load_script_file(
                test_resources / "finalCompanyScriptFullDates.script"
            ),
            load_script_file(
                test_resources / "finalCompanyScriptModifiedDates.script"
            ),
            load_script_file(
                test_resources / "finalCompanyScriptKeepSafePrivateTags.script"
            ),
            load_script_file(
                test_resources / "DicomAnonymizerRemoveAllPrivateTags.script"
            ),
            load_script_file(
                test_resources
                / "DicomAnonymizerRemoveSpecificPrivateTags.script"
            ),
        ]

        # make some context
        dicom_values = Dataset()
        elem = DataElement(
            0x00750010, "LT", "ANONYMIZER"
        )  # Private creator tag
        dicom_values.add(elem)
        elem = DataElement(0x00751079, "LO", "YES")
        dicom_values.add(elem)
        new_dict_items = {
            0x00751079: (
                "CS",
                "1",
                "Retain UIDs Option",
                "",
                "RetainUIDsOption",
            )
        }
        DicomDictionary.update(new_dict_items)
        context = PipelineContext(
            dicom_elements=dicom_values, description="Test"
        )

        pipeline = CTPPipeline(stages=stages)
        resolved_pipeline = pipeline.resolve(context)

        summary = resolved_pipeline.summarize()
        self.assertEqual(len(summary.directives_per_stage), 2)
        self.assertEqual(len(summary.all_actions), 311)

        # just check that this does not crash
        summary.to_string()

        summary_string = resolved_pipeline.generate_summary_string()
        assert summary_string
