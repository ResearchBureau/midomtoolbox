"""Methods and classes for dealing with a single CTP anonymizer configuration
script.
"""

import os
from pathlib import Path
from typing import List
from xml.etree import ElementTree as ET  # noqa: N817

from midomtoolbox.ctp.elements import (
    CTPConfigParameter,
    CTPConfigScriptContext,
    CTPLinePrintable,
    CTPRule,
    Resolvable,
)
from midomtoolbox.ctp.exceptions import CTPScriptDicomTagParseError
from midomtoolbox.ctp.parser import CTPScriptTransformer, ctp_script_parser


class CTPConfigScriptParserError(Exception):
    pass


class CTPConfigElement:
    """a single rule in a CTP dicomfilter script"""

    def __init__(self, element):
        """

        Parameters
        ----------
        element: :obj:`xml.etree.ElementTree.Element`, optional
            Original xml element that is the basis of this parameter. Defaults to
            None.
        """
        self.element = element


class CTPDicomTagAction(Resolvable, CTPConfigElement, CTPLinePrintable):
    """Rule to remove, keep, whatever with a dicom tag"""

    def __init__(self, tag_code, tag_name, rule: CTPRule, element=None):
        """
        Parameters
        ----------
        tag_code: str
            DICOM tag code as hexadicimal, like 0010102e
        tag_name: str
            Dicom Tag name such as 'PatientID'
        rule: CTPRule
            The rule that is to be performed on this tag
        element: :obj:`xml.etree.ElementTree.Element`, optional
            Original xml element that is the basis of this parameter. Defaults
            to None.
        """
        super().__init__(element)
        self.tag_code = tag_code
        self.tag_name = tag_name
        self.rule = rule

    def __str__(self):
        return f"{self.tag_code} - {self.tag_name} : {self.rule}"

    def __lt__(self, other):
        """Built in 'less then'. For sorting"""
        return self.tag_code < other.tag_code

    def contains_skip_command(self):
        """Would this rule  be interpreted as @skip() by CTP?

        In CTP, when the command @skip() is given, all further excution of
         the script file is halted.

        """
        return self.rule.contains_skip_command()

    def ctp_script_string(self):
        """The way that this action is represented inside CTP anonymizer script"""
        return (
            f'<e en="T" t="{self.tag_code}" n="{self.tag_name}">'
            f"{self.rule.ctp_script_string()}</e>"
        )


class CTPTraceableTagAction(CTPDicomTagAction):
    """A tag action that holds the script that it came from"""

    def __init__(
        self, tag_code, tag_name, rule, element=None, parent_script=None
    ):
        """
        Parameters
        ----------
        tag_code: str
            DICOM tag code as hexadicimal, like 0010102e
        tag_name: str
            Dicom Tag name such as 'PatientID'
        rule: str
            Description of the action to take in CTP's notation. This conuld be
             single directive like '@keep' or a full
            if statement like '@if(0075[ANONYMIZER]80,contains,YES)
            {@keep()}{@skip()}'
        element: :obj:`xml.etree.ElementTree.Element`, optional
            Original xml element that is the basis of this parameter. Defaults
             to None.
        parent_script: CTPConfigScript
            The script that this action is coming from
        """
        super().__init__(
            tag_code=tag_code, tag_name=tag_name, rule=rule, element=element
        )
        self.parent_script = parent_script

    def __str__(self):
        return super().__str__() + f" ({self.parent_script.name})"


class CTPDirective(CTPConfigElement):
    """A single line modifier to an anonymizer script. For example 'keep safe
    private', 'remove overlays'

    Made this class to make it comparable so I can remove duplicates
    """

    def __init__(self, key, text, element=None):
        """
        Parameters
        ----------
        key: str
            The identifier for this directive. Like 'privategroups'
        text: str
            Verbose description of this directive. Like 'Keep Private Groups'
        element: :obj:`xml.etree.ElementTree.Element`, optional
            Original xml element that is the basis of this parameter. Defaults
             to None.
        """
        super().__init__(element)
        self.key = key
        self.text = text

    def __str__(self):
        return f"Directive(k) '{self.key}': {self.text}"

    def __eq__(self, other):
        return self.key == other.key

    def __hash__(self):
        return hash(self.key)


class CTPKeepDirective(CTPDirective, CTPLinePrintable):
    """A rule to keep a certain class of DICOM elements, like 'keep private
    groups'
    """

    def ctp_script_string(self):
        """The representation of this element in CTP script
        Returns
        -------
        str:
            how this element would appear in a CTP script
        """
        return f'<k en="F" t="{self.key}">{self.text}</k>'


class CTPRemoveDirective(CTPDirective, CTPLinePrintable):
    """A rule to remove a certain class of DICOM elements, like 'remove overlays'"""

    def ctp_script_string(self):
        """The representation of this element in CTP script
        Returns
        -------
        str:
            how this element would appear in a CTP script
        """
        return f'<k en="F" t="{self.key}">{self.text}</k>'


class CTPConfigScript:
    """Represents the contents of a configuration file for a CTP DICOM filter pipeline
    step
    """

    def __init__(
        self, elements: List[CTPConfigElement], name: str = "unnamed"
    ):
        """Create a representation of a CTP DICOM filter pipeline configuration

        Parameters
        ----------
        elements: :obj:`List[CTPConfigElement]`
            List of each item in script, in order
        name: str, optional
            The name of this script. Used in printing. Defaults to 'unnamed'

        Notes
        -----
        The order in parameter 'elements' is important due to the existence of
        the '@skip()' directive, which will make CTP ignore any directives that.
        """

        self.elements: List[CTPConfigElement] = elements
        self.name = name

    @property
    def parameters(self):
        """
        Returns
        -------
        :obj:`List[CTPConfigParameter]`
            parameters that can be used in other tags in this script
        """
        return [x for x in self.elements if isinstance(x, CTPConfigParameter)]

    @property
    def dicom_tag_actions(self):
        """
        Returns
        -------
        :obj:`List[CTPDicomTagAction]`
            definitions of a single tag, possibly some logic, and what to do
            with that tag
        """
        return [x for x in self.elements if isinstance(x, CTPDicomTagAction)]

    @property
    def keep(self):
        """
        Returns
        -------
        keep: :obj:`List[CTPKeepDirective]`
            directives to keep a larger group of DICOM tags, defined in CTP

        """
        return [x for x in self.elements if isinstance(x, CTPKeepDirective)]

    @property
    def remove(self):
        """
        Returns
        -------
        :obj:`List[CTPRemoveDirective]`
            directives to remove a larger group of DICOM tags, defined in CTP

        """
        return [x for x in self.elements if isinstance(x, CTPRemoveDirective)]

    @property
    def directives(self):
        """Directives are broad-stroke commands in a script to keep or remove
        certain classes of tags

        Returns
        -------
        :obj:`List[CTPRemoveDirective]`
            all directives to keep or remove a larger group of DICOM tags
        """
        return self.remove + self.keep

    def resolve(self, context: CTPConfigScriptContext):
        """Given the context, simplify the script as much as possible. Fill
        in parameters, resolve if statements etc. Truncate anything after @skip()

        Parameters
        ----------
        context: CTPConfigScriptContext
            context to resolve with

        Returns
        -------
        CTPResolvedConfigScript
            The same script with full resolution done
        """
        resolved_elements = []
        for element in self.elements:
            if isinstance(element, CTPDicomTagAction):
                element.resolve(context)
                if element.contains_skip_command():
                    break
                else:
                    resolved_elements.append(element)
            else:
                # ignoring reasonable mypy objections. This is old legacy code.
                resolved_elements.append(element)  # type: ignore[arg-type]

        return CTPResolvedConfigScript(
            elements=resolved_elements, context=context, name=self.name  # type: ignore[arg-type]
        )

    def __str__(self):
        return f"Config script '{self.name}'"


class CTPResolvedConfigScript(CTPConfigScript):
    """A CTP DICOM filter pipeline script for which @if and other variables have
    been resolved as far as possible

    Notes
    -----
    A resolved script might contain less elements then the original, due to the
    @skip() directive, Which can truncate
    applying any more directives after it
    """

    def __init__(
        self, elements: List[CTPConfigElement], context, name: str = "Unnamed"
    ):
        """

        Parameters
        ----------
        elements: :obj:`List[CTPConfigElement]`
            List of each item in script, in order
        context: CTPConfigScriptContext
            the context with which the resolution was done
        name: str, optional
            The name of this script. Used in printing. Defaults to 'unnamed'

        Notes
        -----
        The context with which this script has been resolved is not saved because
        it is not quite clear whether an entire script has an unambiguous context
        in midomtoolbox.ctp. The documentation is not sufficient to determine the
        resolution precedence of different elements. But as at tag with @skip()
        in it will halt any further execution I assume each tag is precessed in
        order. Each the context for each individual resolved element is saved
        with that element in element.original_with_context
        """
        super().__init__(elements=elements, name=name)
        self.context = context


class CTPConfigScriptFile:
    """XML file with configuration options. Can be parsed into CTPConfigScript"""

    def __init__(self, path):
        """Create a scriptfile object related to the file at path

        Parameters
        ----------
        path: str
            read this script file

        """
        self.path = path

    @staticmethod
    def parse_element(element):
        """Try to parse a single CTP script file xml element

        Parameters
        ----------
        element: :obj:`xml.etree.ElementTree.Element`
            The element to parse. Should be valid CTP script

        Returns
        -------
        CTPConfigElement:
            The object equivalent to the input XML

        Raises
        ------
        CTPScriptDicomTagParseError
            If element cannot be parsed to any object

        """

        if element.tag == "p":
            # parameter. Example <p t="UIDROOT">1.2.3.4</p>
            return CTPConfigParameter(
                name=element.attrib["t"], value=element.text
            )
        elif element.tag == "e":
            # A tag directive. Example: <e en="T" t="00751070"
            # n="BasicConfidentiallyProfile">@remove()</e>
            parsed_rule = ctp_script_parser.parse(element.text)
            transformed_rule = CTPScriptTransformer().transform(parsed_rule)
            return CTPDicomTagAction(
                tag_code=element.attrib["t"],
                tag_name=element.attrib["n"],
                rule=transformed_rule,
            )
        elif element.tag == "k":
            # A keep directive such as <r en="T" t="privategroups">Remove
            # private groups</r>
            return CTPKeepDirective(key=element.attrib["t"], text=element.text)
        elif element.tag == "r":
            # A removal directive such as <r en="T" t="privategroups">Remove
            # private groups</r>
            return CTPRemoveDirective(
                key=element.attrib["t"], text=element.text
            )
        else:
            msg = (
                f"Could not parse xml element '{element}' into any known "
                f"CTP script elemement"
            )
            raise CTPScriptDicomTagParseError(msg)

    def parse(self):
        """Read in this script file and try to parse all elements

        Returns
        -------
        CTPConfigScript
            A representation of this script

        Raises
        ------
        CTPScriptDicomTagParseError
            If any element in this script cannot be parsed
        """
        parsed_tree = ET.parse(self.path)
        script_root = parsed_tree.getroot()
        if not script_root.tag == "script":
            msg = (
                f"Root element of '{self.path}' should be 'script'. Found "
                f"'{script_root.tag}' instead"
            )
            raise CTPConfigScriptParserError(msg)

        xml_elements = [x for x in script_root]
        elements = [self.parse_element(x) for x in xml_elements]

        return CTPConfigScript(
            elements=elements, name=os.path.basename(self.path)
        )


def load_script_file(path: Path):
    """Quick way to load an parse a CTP configuration file

    Parameters
    ----------
    path: :obj:`pathlib.Path`
        read this script file

    Returns
    -------
    CTPConfigScript
        A representation of this script

    Raises
    ------
    CTPScriptDicomTagParseError
        If any element in this script cannot be parsed

    """
    return CTPConfigScriptFile(path=path.resolve()).parse()
