"""Classes and functions relating to PrivateTagDictionary.xml, the file that
CTP uses to record known private tags
"""

from typing import List
from xml.etree import ElementTree

from pydicom import Dataset

from midomtoolbox.ctp.elements import CTPConfigScriptContext, CTPDicomTag
from midomtoolbox.ctp.exceptions import CTPScriptDicomTagParseError


class TagDictionaryParseException(Exception):
    pass


class CTPDicomElementSchema:
    """A definition of what a dicom tag should be like, but without value. Typically
    used to define private tag dictionary
    """

    def __init__(self, tag_string, VR, tag_key="", VM=1):  # noqa: N803
        """

        Parameters
        ----------
        tag_string: str
            dicom tag like, '101011e8', or something that needs resolving like
            '0075[ANONYMIZER]81'
        VR: str
            Value representation of this tag
        tag_key: str, optional
            string representation of this tag, like 'Modality'. Defaults to tag_string
        VM: int, optional
            Value multiplicity of this tag. How many values are expected in value?
            defaults to 1
        value: int or str, optional
            value of this element, defaults to None

        """
        self.tag = CTPDicomTag(tag_string)
        self.VR = VR
        if not tag_key:
            tag_key = tag_string
        self.tag_key = tag_key
        self.VM = VM

    def __str__(self):
        return f"{self.tag} ({self.VR})"

    def resolve(self, dicom_elements: Dataset):
        """Try to a CTP dicom tag into a canonical hex string like '00751081'.
        A CTP dicom tag can be like '0075[ANONYMIZER]81' or like
        'Modality' or like '00751081'

        Parameters
        ----------
        dicom_elements: Dataset
            The context to use to resolve this tag

        Returns
        -------
        CTPDicomElementSchema
            schema with resolved tag

        Raises
        ------
        CTPScriptDicomTagParseError
            If this tag cannot be resolved into canonical form

        """
        context = CTPConfigScriptContext(dicom_values=dicom_elements)
        self.tag.resolve(context)
        return CTPDicomElementSchema(
            tag_string=self.tag.tag_string,
            VR=self.VR,
            tag_key=self.tag_key,
            VM=self.VM,
        )


class CTPTagDictionary:
    """Collection of CTP DICOM element descriptions. This describes the tag, name
    datatype of dicom tags. Can contain unresolved tag names such as `0075[CREATOR]01`

    """

    def __init__(self, elements: List[CTPDicomElementSchema]):
        """

        Parameters
        ----------
        elements: List[CTPDicomElementSchema]
            List of descriptions of each DICOM element
        """
        self.elements = elements

    def resolve(self, dicom_elements: Dataset):
        """Resolve the tags in this dictionary as far as possible. Discard tags that
        cannot be resolved

        Parameters
        ----------
        dicom_elements: Dataset
            context with which this dictionary has been resolved

        Returns
        -------
        ResolvedCTPTagDictionary
            Containing all elements that could be resolved
        """
        resolved = []
        for element in self.elements:
            try:
                resolved.append(element.resolve(dicom_elements=dicom_elements))
            except CTPScriptDicomTagParseError:
                # if you cant parse, just skip
                pass

        return ResolvedCTPTagDictionary(
            context=dicom_elements, elements=resolved
        )


class ResolvedCTPTagDictionary(CTPTagDictionary):
    """Like a dictionary, but all tags are resolved, which means they have canonical
    form like '00751001' and not '0075[CREATOR]01'
    """

    def __init__(self, context, elements):
        """

        Parameters
        ----------
        context: :obj:`CTPConfigScriptContext`
            the context that was used to resolve this dictionary
        elements: List[CTPDicomElementSchema]
            List of descriptions of each DICOM element
        """
        super().__init__(elements)
        self.context = context

    def add_to_pydicom_dictionary(self, dicom_dictionary, keyword_dict):
        """Add this tag dictionary to a pydicom dictionary, so that you can use the
        tags in this dictionary
        within pydicom.

        Parameters
        ----------
        dicom_dictionary: Dict
            The dict you import from pydicom.datadict.DicomDictionary
        keyword_dict: Dict
            The dict you import from pydicom.datadict.keyword_dict

        Examples
        --------
        >>> # import these two dics from pydicom to modify later
        >>> from pydicom.datadict import DicomDictionary, keyword_dict
        >>>
        >>> # create a context containing a single private creator tag,
        >>> # claiming group 11 for 'ANONYMIZER'
        >>> dicom_values = Dataset()
        >>> dicom_values.add(DataElement(0x00750011, 'LT', 'ANONYMIZER'))
        >>>
        >>> # use this context to resolve tags like '0075[ANONYMIZER]01'
        to '00751101'
        >>> private_dict = private_dict_raw.resolve(context=dicom_values)
        >>>
        >>> # add all resolved tags to dictionary to be able to use the private
        tags in pydicom
        >>> private_dict.add_to_pydicom_dictionary(DicomDictionary, keyword_dict)

        Notes
        -----
        This whole method is a bit stinky because it modifies imports. But I see
        no other way to do this properly
        currently, and it follows exactly the example here:
        https://pydicom.github.io/pydicom/stable/auto_examples/metadata_processing
        /plot_add_dict_entries.html

        Returns
        -------
        Nothing, just updates the input
        """

        new_items = {
            int(el.tag.tag_string, 16): (
                el.VR,
                el.VM,
                el.tag_key,
                "",
                el.tag_key,
            )
            for el in self.elements
        }
        # Update the dictionary itself
        dicom_dictionary.update(new_items)
        # Update the reverse mapping from name to tag
        new_names_dict = {val[4]: tag for tag, val in new_items.items()}
        keyword_dict.update(new_names_dict)

        return dicom_dictionary, keyword_dict


class TagDictionaryFile:
    def __init__(self, path):
        """

        Parameters
        ----------
        path: str
            full path to a PrivateTagDictionary.xml file
        """
        self.path = path

    @staticmethod
    def parse_element(element: ElementTree.Element):
        """Parse single element in dictionary file

        Returns
        -------
        CTPDicomTag

        """
        tag_string = (
            f"{element.attrib['gp']}[{element.attrib['cr']}]"
            f"{element.attrib['el']}"
        )
        tag = CTPDicomElementSchema(
            tag_string=tag_string,
            VR=element.attrib["vr"],
            tag_key=element.attrib["key"],
            VM=element.attrib["vm"],
        )
        return tag

    def parse(self):
        """Parse this private tag dictionary file into a python object

        Returns
        -------
        CTPTagDictionary
            The dict file parsed

        Raises
        ------
        TagDictionaryParseException
            When parsing fails

        """
        parsed_tree = ElementTree.parse(self.path)
        script_root = parsed_tree.getroot()
        if not script_root.tag == "dictionary":
            msg = (
                f"Root element of '{self.path}' should be 'dictionary'. "
                f"Found '{script_root.tag}' instead"
            )
            raise TagDictionaryParseException(msg)
        xml_elements = script_root.find("elements")
        if not xml_elements:
            msg = (
                f"Root/dictionary element of '{self.path}' should contains element "
                f"'elements' but I could not find "
                f"that"
            )
            raise TagDictionaryParseException(msg)

        elements = [self.parse_element(x) for x in xml_elements]
        return CTPTagDictionary(elements=elements)
