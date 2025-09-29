import unittest

from pydicom import DataElement, Dataset

from midomtoolbox.ctp.elements import (
    CTPConfigParameter,
    CTPConfigScriptContext,
    CTPDicomTag,
    Contains,
    Equals,
    Exists,
    IsBlank,
)
from midomtoolbox.ctp.exceptions import CTPScriptDicomTagParseError
from midomtoolbox.ctp.parser import (
    CTPScriptParser,
    CTPScriptTransformer,
    ctp_script_parser,
)
from tests.conftest import TestResourcesFolder


class ElementTests(unittest.TestCase):
    def setUp(self):
        self.test_resources_folder = TestResourcesFolder(
            __file__, r"test_resources"
        )

    def test_rule_resolution(self):

        rule_string = (
            "@if(Modality,equals,MR){MR}{}@if(root:0075"
            "[ANONYMIZER]76,contains,YES){MODIFIED}{@VAR}"
        )

        parser = CTPScriptParser()
        rule = parser.parse(rule_string)

        dicom_values = Dataset()
        context = CTPConfigScriptContext(dicom_values=dicom_values)

        # Nothing can be resolved with empty context, the script string should be
        # unaltered
        self.assertEqual(rule.ctp_script_string(), rule_string)

        # trying to resolve without enough information to resolve should raise an
        # error
        self.assertRaises(CTPScriptDicomTagParseError, rule.resolve, context)

        # With a private creator, the tag can be simplefied
        context.dicom_values.add(DataElement(0x00750010, "LT", "ANONYMIZER"))
        context.dicom_values.add(DataElement(0x00751076, "LO", "YES"))

        rule.resolve(context)
        self.assertEqual(rule.ctp_script_string(), "MODIFIED")

        # Change value so if statement resolves to other side
        context.dicom_values[0x00751076].value = "NO"
        rule.resolve(context)
        self.assertEqual(rule.ctp_script_string(), "@VAR")

        # Var can also be simplified, if it is defined in context
        context.parameters.append(
            CTPConfigParameter(name="VAR", value="1.2.3.4.5")
        )
        rule.resolve(context)
        self.assertEqual("1.2.3.4.5", rule.ctp_script_string())

    def test_rule_if_resolution(self):

        rule_string = "@if(0075[ANONYMIZER]76,contains,YES){MODIFIED}{@VAR}"
        parsed = ctp_script_parser.parse(rule_string)
        rule = CTPScriptTransformer().transform(parsed)

        context = CTPConfigScriptContext(dicom_values=Dataset())
        # With a private creator, the tag can be simplefied
        context.dicom_values.add(DataElement(0x00750010, "LT", "ANONYMIZER"))
        context.dicom_values.add(DataElement(0x00751076, "LO", "YES"))

        rule.resolve(context)
        self.assertEqual(rule.ctp_script_string(), "MODIFIED")

    def test_rule_if_resolution_2(self):
        rule_string = "@if(Modality,equals,MR){MR}{}"
        parsed = ctp_script_parser.parse(rule_string)
        rule = CTPScriptTransformer().transform(parsed)

        context = CTPConfigScriptContext(dicom_values=Dataset())

        rule.resolve(context)
        self.assertEqual(rule.ctp_script_string(), "")

    def test_ctp_rule_parser_resolve(self):
        """Check whether private creator names are being replaced as expected in
        CTP dicom tags
        """

        # create some context
        dicom_values = Dataset()
        elem = DataElement(
            0x00750010, "LT", "ANONYMIZER"
        )  # Private creator tag
        dicom_values.add(elem)
        elem = DataElement(0x00751079, "LO", "YES")
        dicom_values.add(elem)

        context = CTPConfigScriptContext(dicom_values=dicom_values)

        parser = CTPScriptParser()
        rule = parser.parse(
            r"@if(root:0075[ANONYMIZER]77,contains,YES){@keep()}{@remove()}"
        )
        # In this context 00751077 is not set, so the result should be the 'else'
        # result
        rule.resolve(context=context)
        self.assertEqual(rule.ctp_script_string(), "@remove()")

        # add the -77 element with value YES. Not the result should be @keep
        elem = DataElement(0x00751077, "LO", "YES")
        dicom_values.add(elem)
        rule.resolve(context=context)
        self.assertEqual(rule.ctp_script_string(), "@keep()")

        # now set the value, but to NO, so the rule should yield @remove() again
        elem = DataElement(0x00751077, "LO", "NO")
        dicom_values.add(elem)
        rule.resolve(context=context)
        self.assertEqual(rule.ctp_script_string(), "@remove()")

    def test_ctp_expression_contains(self):
        # create some context
        dicom_values = Dataset()
        elem = DataElement(
            0x00750010, "LT", "ANONYMIZER"
        )  # Private creator tag
        dicom_values.add(elem)
        elem = DataElement(0x00751077, "LO", "YES")
        dicom_values.add(elem)

        expression = Contains(
            CTPDicomTag(tag_string="0075[ANONYMIZER]77"), value="YES"
        )

        context = CTPConfigScriptContext(dicom_values=dicom_values)
        expression.resolve(context=context)
        self.assertTrue(expression.is_true(context))

    def test_ctp_expression_matches(self):
        # create some context
        dicom_values = Dataset()
        elem = DataElement(
            0x00750010, "LT", "ANONYMIZER"
        )  # Private creator tag
        dicom_values.add(elem)
        elem = DataElement(0x00751077, "LO", "YES")
        dicom_values.add(elem)

        parser = CTPScriptParser()
        rule = parser.parse(
            '@if(Modality,matches,"MR|PT|CT"){@keep()}{@remove()}'
        )

        context = CTPConfigScriptContext(dicom_values=dicom_values)
        rule.resolve(context)

        # get the Matches() expression from the parsed rule
        expression = rule.line_elements[0].rule_if
        # This should be false, because there is no modality to match
        self.assertFalse(expression.is_true(context))

        # now add a modality to context
        context.dicom_values.Modality = "CRAZY_MODALITY"
        # still should be false because it does not match the expression
        self.assertFalse(expression.is_true(context))

        # But with MR it should be true
        context.dicom_values.Modality = "MR"
        self.assertTrue(expression.is_true(context))

    def test_ctp_expressions(self):
        """Test some rules like contains() and exists() and isblank()"""
        # create some context. There is only two tags
        dicom_values = Dataset()
        elem = DataElement(0x0010123E, "LO", "")
        dicom_values.add(elem)
        elem = DataElement(0x10102222, "LO", "some_content")
        dicom_values.add(elem)
        dicom_values.Modality = "MR"

        context = CTPConfigScriptContext(dicom_values=dicom_values)
        # A defined tags should exist, non-defined tags should not exist
        self.assertTrue(
            Exists(CTPDicomTag("0010123e")).is_true(context=context)
        )
        self.assertFalse(
            Exists(CTPDicomTag("12345678")).is_true(context=context)
        )

        # Testing contains on a non-existant tag should still be false
        self.assertFalse(
            Contains(CTPDicomTag("12345673"), "YES").is_true(context=context)
        )

        # this tag exists but it empty
        self.assertFalse(
            Contains(CTPDicomTag("0010123e"), "YES").is_true(context=context)
        )
        self.assertTrue(
            IsBlank(CTPDicomTag("0010123e")).is_true(context=context)
        )

        # this tag exists and is not empty
        self.assertFalse(
            IsBlank(CTPDicomTag("10102222")).is_true(context=context)
        )
        self.assertTrue(
            Contains(CTPDicomTag("10102222"), "content").is_true(
                context=context
            )
        )
        self.assertFalse(
            Contains(CTPDicomTag("10102222"), "other").is_true(context=context)
        )

        # a non-existant tags are considered blank
        self.assertTrue(
            IsBlank(CTPDicomTag("12345565")).is_true(context=context)
        )

        # test resolving by tag name
        self.assertTrue(
            Equals(CTPDicomTag("Modality"), "MR").is_true(context=context)
        )
