import unittest

from pydicom import DataElement, Dataset
from pydicom.datadict import DicomDictionary, keyword_dict

from midomtoolbox.ctp.tagdictionary import TagDictionaryFile
from tests.conftest import TestResourcesFolder


class DicomFileTester(unittest.TestCase):
    def setUp(self):
        self.test_resources_folder = TestResourcesFolder(
            __file__, r"test_resources"
        )

    def test_parse_tag_dictionary(self):
        dict_file = TagDictionaryFile(
            path=self.test_resources_folder.get_path(
                "PrivateTagDictionary.xml"
            )
        )
        private_dict_raw = dict_file.parse()

        # create some context
        dicom_values = Dataset()
        dicom_values.add(DataElement(0x00750011, "LT", "ANONYMIZER"))

        # resolve tags with [ANONYMIZER] in them given the private
        # creator tag
        private_dict = private_dict_raw.resolve(dicom_elements=dicom_values)

        # add all resolved tags to pydicom
        private_dict.add_to_pydicom_dictionary(DicomDictionary, keyword_dict)

        # now it should be possible to use the custom private tags in regular
        # pydicom operations:
        dicom_values.PatientName = "Clementine"
        dicom_values.AnonymizedPatientName = "Pseudo-Clementine"
        dicom_values.unknownTag = "some value"

        # check that the values have actually been set.
        # this standard tag should work regardless of any additions
        self.assertEqual(
            dicom_values.data_element("PatientName").value, "Clementine"
        )
        # this is defined in the private tag dict and should work
        self.assertEqual(
            dicom_values.data_element("AnonymizedPatientName").value,
            "Pseudo-Clementine",
        )
        self.assertEqual(
            dicom_values.data_element("AnonymizedPatientName").VR, "PN"
        )
        # Sanity check: this element should not exist because it is not defined
        # anywhere in dictionary
        self.assertIsNone(dicom_values.data_element("unknownTag"))
