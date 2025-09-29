"""Some useful contexts for resolving a pipeline"""

from pydicom import DataElement, Dataset

from midomtoolbox.ctp.pipeline import PipelineContext


class WetenschapAlgemeenContext(PipelineContext):
    """Standard dicom tags for a file processed with the Wetenschap-algemeen project

    tag_number:0x70,nameBasicConfidentiallyProfile,useTrue
    tag_number:0x71,nameCleanPixelDataOption,useTrue
    tag_number:0x72,nameCleanRecognizableVisualFeaturesOption,useFalse
    tag_number:0x73,nameCleanGraphicsOption,useFalse
    tag_number:0x74,nameCleanStructuredContentOption,useFalse
    tag_number:0x75,nameCleanDescriptorsOption,useTrue
    tag_number:0x76,nameRetainLongitudinalTemporalInformationWithFullDatesOptions,useTrue
    tag_number:0x77,nameRetainPatientCharacteristicsOption,useFalse
    tag_number:0x78,nameRetainDeviceIdentityOption,useTrue
    tag_number:0x79,nameRetainUIDsOption,useFalse
    tag_number:0x80,nameRetainSafePrivateOption,useTrue
    tag_number:0x81,nameRetainLongitudinalTemporalInformationWithModifiedDatesOptions,useFalse
    """

    def __init__(self, modality=None):
        """

        Parameters
        ----------
        modality: str, optional
            Set this modality in context

        """
        description = "Project wetenschap-algemeen"
        dicom_elements = self.get_wetenschap_algemeen_elements()

        if modality:
            description = description + f" (Modality '{modality}')"
            dicom_elements.Modality = modality

        super().__init__(
            dicom_elements=dicom_elements, description=description
        )

    def get_wetenschap_algemeen_elements(self):
        dicom_elements = Dataset()
        dicom_elements.add(DataElement(0x00750010, "LT", "ANONYMIZER"))

        dicom_elements.add(DataElement(0x00751070, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751071, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751072, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751073, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751074, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751075, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751076, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751077, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751078, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751079, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751080, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751081, "LO", "NO"))

        # this last element is set in AnonBase.script but determines the removal of
        # all dates later. This library does not support logic based on setting
        # internal tag as that would almost re-implement CTP in python.
        # see notes maintenance/scriptview.py line 120
        dicom_elements.add(DataElement(0x00751082, "LO", "YES"))
        return dicom_elements


class PieternelRDSRContext(PipelineContext):
    """Pieternel context identical to wetenschap algemeen but with cleanstructured
    content = True
    """

    def __init__(self, modality=None):
        """

        Parameters
        ----------
        modality: str, optional
            Set this modality in context

        """
        description = "Project wetenschap-algemeen"
        dicom_elements = self.get_wetenschap_algemeen_elements()

        if modality:
            description = description + f" (Modality '{modality}')"
            dicom_elements.Modality = modality

        super().__init__(
            dicom_elements=dicom_elements, description=description
        )

    def get_wetenschap_algemeen_elements(self):
        dicom_elements = Dataset()
        dicom_elements.add(DataElement(0x00750010, "LT", "ANONYMIZER"))

        dicom_elements.add(DataElement(0x00751070, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751071, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751072, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751073, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751074, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751075, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751076, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751077, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751078, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751079, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751080, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751081, "LO", "NO"))

        # this last element is set in AnonBase.script but determines the removal of
        # all dates later. This library does not support logic based on setting
        # internal tag as that would almost re-implement CTP in python.
        # see notes maintenance/scriptview.py line 120
        dicom_elements.add(DataElement(0x00751082, "LO", "YES"))
        return dicom_elements


class AnonLevel3Context(PipelineContext):
    """Standard profile in research bureau, one step more stringent than
    wetenschap-algemeen (which is level_4)

    """

    def __init__(self, modality=None):
        """

        Parameters
        ----------
        modality: str, optional
            Set this modality in context

        """
        description = "Anon_level_3"
        dicom_elements = self.get_wetenschap_algemeen_elements()

        if modality:
            description = description + f" (Modality '{modality}')"
            dicom_elements.Modality = modality

        super().__init__(
            dicom_elements=dicom_elements, description=description
        )

    def get_wetenschap_algemeen_elements(self):
        dicom_elements = Dataset()
        dicom_elements.add(DataElement(0x00750010, "LT", "ANONYMIZER"))

        dicom_elements.add(DataElement(0x00751070, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751071, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751072, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751073, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751074, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751075, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751076, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751077, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751078, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751079, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751080, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751081, "LO", "YES"))

        # this last element is set in AnonBase.script but determines the removal of
        # all dates later. This library does not support logic based on setting
        # internal tag as that would almost re-implement CTP in python.
        # see notes maintenance/scriptview.py line 120
        dicom_elements.add(DataElement(0x00751082, "LO", "YES"))
        return dicom_elements


class AnonLevel2Context(PipelineContext):
    """Standard profile in research bureau, one step more stringent than
    level 3
    """

    def __init__(self, modality=None):
        """

        Parameters
        ----------
        modality: str, optional
            Set this modality in context

        """
        description = "Anon_level_2"
        dicom_elements = self.get_wetenschap_algemeen_elements()

        if modality:
            description = description + f" (Modality '{modality}')"
            dicom_elements.Modality = modality

        super().__init__(
            dicom_elements=dicom_elements, description=description
        )

    def get_wetenschap_algemeen_elements(self):
        dicom_elements = Dataset()
        dicom_elements.add(DataElement(0x00750010, "LT", "ANONYMIZER"))

        dicom_elements.add(DataElement(0x00751070, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751071, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751072, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751073, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751074, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751075, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751076, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751077, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751078, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751079, "LO", "NO"))
        dicom_elements.add(DataElement(0x00751080, "LO", "YES"))
        dicom_elements.add(DataElement(0x00751081, "LO", "NO"))

        # this last element is set in AnonBase.script but determines the removal of
        # all dates later. This library does not support logic based on setting
        # internal tag as that would almost re-implement CTP in python.
        # see notes maintenance/scriptview.py line 120
        dicom_elements.add(DataElement(0x00751082, "LO", "YES"))
        return dicom_elements
