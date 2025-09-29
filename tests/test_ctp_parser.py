import unittest

from pydicom import Dataset

from midomtoolbox.ctp.elements import (
    CTPConfigParameter,
    CTPConfigScriptContext,
)
from midomtoolbox.ctp.parser import (
    CTPScriptParser,
    CTPScriptParserException,
)
from tests.conftest import TestResourcesFolder


class ParserTester(unittest.TestCase):
    def setUp(self):
        self.test_resources_folder = TestResourcesFolder(
            __file__, r"test_resources"
        )

    def test_rule_parsing(self):
        parser = CTPScriptParser()
        rule_string = (
            "@if(modality,equals,MR){MR}{}@if(root:0075"
            "[ANONYMIZER]76,contains,YES){MODIFIED}{@VAR}"
        )
        rule = parser.parse(rule_string)

        reconstructed = rule.ctp_script_string()
        self.assertEqual(rule_string, reconstructed)

    def test_ctp_rule_parser(self):
        """Check whether rules are being parsed into the correct objects"""

        parser = CTPScriptParser()
        # try a valid @if rule
        rule = parser.parse(
            r"@if(root:0075[ANONYMIZER]77,contains,YES){@keep()}{@remove()}"
        )

        if_function = rule.line_elements[0]
        self.assertEqual(
            if_function.rule_else.ctp_script_string(), "@remove()"
        )
        self.assertEqual(
            if_function.rule_if.ctp_script_string(),
            "(root:0075[ANONYMIZER]77,contains,YES)",
        )
        self.assertEqual(if_function.rule_then.ctp_script_string(), "@keep()")

        # try a non-if rule. When resolving this it should just print the original
        # text
        context = CTPConfigScriptContext(dicom_values=Dataset())
        rule = parser.parse(r"@remove()")
        rule.resolve(context)
        self.assertEqual(rule.ctp_script_string(), "@remove()")

        # try an invalid rule.
        self.assertRaises(
            CTPScriptParserException, parser.parse, r"@if(root)invalid"
        )

    def test_ctp_rule_non_if_resolution(self):
        """Verify that non-if functions that contain parameters are still resolved"""

        parser = CTPScriptParser()
        rule = parser.parse(r"@incrementdate(this,@DATEINC)")

        context = CTPConfigScriptContext(
            dicom_values=Dataset(),
            parameters=[CTPConfigParameter(name="DATEINC", value="99")],
        )
        rule.resolve(context)
        self.assertEqual("@incrementdate(this,99)", rule.ctp_script_string())
