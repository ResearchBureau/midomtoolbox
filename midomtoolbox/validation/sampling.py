"""Creating and working with examples of DICOM datasets and dataset transformations"""
import json
import random
import string
from functools import partial
from typing import Any, ClassVar, List

import numpy as np
from dicomgenerator.pixeldata import Block, add_blocks, draw_noise
from midom.components import PixelArea
from midom.validation import deepcopy_fix
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator
from pydicom import Dataset, FileMetaDataset
from pydicom.tag import Tag
from pydicom.uid import ExplicitVRLittleEndian

from midomtoolbox.logs import get_module_logger

logger = get_module_logger("sampling")


def get_pixel_dtype_ds(ds: Dataset) -> np.dtype:
    return get_pixel_dtype(
        bits_allocated=ds.BitsAllocated,
        pixel_representation_signed=ds.PixelRepresentation,  # 1=signed, 0=unsigned
    )


def get_pixel_dtype(
    bits_allocated: int, pixel_representation_signed: bool
) -> np.dtype:
    """
    Infer the correct numpy dtype for the PixelData of a DICOM dataset.

    Relies on:
      - BitsAllocated  (0028,0100): storage width in bits (8, 16, 32, 64)
      - PixelRepresentation (0028,0103): 0 = unsigned, 1 = signed
    """

    dtype_map = {
        (8, False): np.uint8,
        (8, True): np.int8,
        (16, False): np.uint16,
        (16, True): np.int16,
        (32, False): np.uint32,
        (32, True): np.int32,
        (64, False): np.uint64,
        (64, True): np.int64,
    }

    dtype = dtype_map.get((bits_allocated, pixel_representation_signed))
    if dtype is None:
        raise ValueError(
            f"Unsupported BitsAllocated={bits_allocated}, "
            f"PixelRepresentation={pixel_representation_signed}"
        )

    return np.dtype(dtype)


def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    return "".join(random.choices(characters, k=length))


class PixelNoiseURI(BaseModel):
    """
    A parsed representation of a PixelNoise URI.

    Encapsulates the parameters encoded in a ``pixelnoise://`` URI string,
    describing a noise image's dimensions, numeric type, and random seed.

    Parameters
    ----------
    height : int
        Height of the noise image in pixels.
    width : int
        Width of the noise image in pixels.
    bit_depth : str
        Numeric data type of the pixel values (e.g. ``'uint8'``, ``'uint16'``,
        ``'float32'``).
    seed : str
        Seed string used to initialise the noise generator.

    Methods
    -------
    from_string(uri)
        Construct a ``PixelNoiseURI`` by parsing a ``pixelnoise://`` URI string.

    Examples
    --------
    >>> uri = PixelNoiseURI.from_string("pixelnoise://100/300/uint8/aseed")
    >>> uri.height
    100
    >>> uri.width
    300
    >>> uri.bit_depth
    'uint8'
    >>> uri.seed
    'aseed'

    Raises
    ------
    ValueError
        If the URI does not start with ``pixelnoise://`` or does not contain
        exactly four slash-separated fields.
    pydantic.ValidationError
        If ``height`` or ``width`` cannot be coerced to ``int``.
    """

    URI_PREFIX: ClassVar[str] = "pixelnoise://"

    height: int
    width: int
    bit_depth: str
    seed: str

    @classmethod
    def from_string(cls, uri: str) -> "PixelNoiseURI":
        if not uri.startswith(cls.URI_PREFIX):
            raise ValueError(f"URI must start with '{cls.URI_PREFIX}'")

        params = uri[len(cls.URI_PREFIX) :]
        parts = params.split("/")

        if len(parts) != 4:
            raise ValueError(
                f"Expected 4 slash-separated values, got {len(parts)}"
            )

        height_str, width_str, bit_depth, seed = parts

        return cls(
            height=int(height_str),
            width=int(width_str),
            bit_depth=bit_depth,
            seed=seed,
        )

    def to_string(self) -> str:
        return (
            f"{self.URI_PREFIX}{self.height}/{self.width}/{self.bit_depth}/"
            f"{self.seed}"
        )


class SampleDataSerializer:
    """A pydicom Dataset JSON serializer that supports writing noise images

    Behaves as the regular pydicom json serializer, but in addition, supports BulkData
    elements of the form 'pixelnoise://' which encodes seeded noise of a certain depth
    and size.

    Useful when validating deidentifiers that process image data. For this you often
    need DICOM examples that have very specific elements, for filters to act upon
    (which 'type' of DICOM image is this). In addition, you need to have PixelData to
    process, with the correct shape, but the actual contents often do no matter, or
    need to be actively removed as they might contain burnt in patient data

    This Serializer allows one to save whole datasets as JSON, but encode the
    PixelData element as white noise of a certain bit depth. This can then be
    transparently loaded again.

    Some properties
    * Only 2d for now
    * Only PixelData, no other elements for now
    * Noise is based on a seed in the URI; loading the same dataset twice will yield
    the same noise pattern.

    Notes
    -----
    Decided to make this into a class instead of a module because I prefer the
    explicit initialisation in code over just an import at the top of the file. This
    serialization is potentially information-destroying, so I prefer explicit init.
    """

    PIXEL_DATA_TAGS = (Tag(0x7FE00010),)  # Pixel Data

    @classmethod
    def dump_handler(cls, json_dict) -> str:
        """Return a PixelNoiseURI for pixel data elements"""

        # these values are needed for generating correct noise size and depth
        rows = json_dict.get(Tag("Rows").json_key)["Value"][0]
        columns = json_dict.get(Tag("Columns").json_key)["Value"][0]
        bits = json_dict.get(Tag("BitsAllocated").json_key)["Value"][0]
        signed = json_dict.get(Tag("PixelRepresentation").json_key)["Value"][0]

        for x in cls.PIXEL_DATA_TAGS:
            element = json_dict.get(x.json_key)
            # replace contents with PixelNoiseURI
            if element:
                new_value = PixelNoiseURI(
                    width=rows,
                    height=columns,
                    bit_depth=get_pixel_dtype(bits, signed).name,
                    seed=generate_random_string(),
                )
                json_dict[x.json_key] = {
                    "vr": element["vr"],
                    "BulkDataURI": new_value.to_string(),
                }

        return json.dumps(json_dict, indent=2)

    @classmethod
    def bulk_data_reader(cls, tag, vr, bulk_data_uri):
        if tag in (x.json_key for x in cls.PIXEL_DATA_TAGS):
            try:
                uri = PixelNoiseURI.from_string(bulk_data_uri)
                return draw_noise(
                    uri.width, uri.height, uri.bit_depth, seed=uri.seed
                ).tobytes()
            except ValueError as e:
                logger.warning(
                    f"Could not parse PixelData element as PixelNoiseURI. "
                    f"Skipping. Error: {e}"
                )
                return None

        else:
            return None

    @classmethod
    def to_json(
        cls, ds: Dataset, replace_with_pixel_noise: bool = True
    ) -> str:
        """

        Parameters
        ----------
        ds: Dataset
            The Dataset to write as Json
        replace_with_pixel_noise: bool, optional
            If true, replace PixelData element (7FE0,0010) with white noise. Will
            write additional DICOM elements such as bit depth if required and not
            present. Defaults to True.

        Returns
        -------
        str
            JSON representation of dataset

        Raises
        ------
        ValueError
        If transfer syntax UID is anything but ExplicitVRLittleEndian
        """

        if ds.file_meta.TransferSyntaxUID != ExplicitVRLittleEndian:
            raise ValueError(
                f"SampleDataSerializer can only handle "
                f"ExplicitVRLittleEndian transfer syntax. "
                f"Found {ds.file_meta.TransferSyntaxUID}"
            )

        if replace_with_pixel_noise:
            return ds.to_json(dump_handler=cls.dump_handler)
        else:
            return ds.to_json(dump_handler=partial(json.dumps, indent=2))

    @classmethod
    def to_dataset(cls, json_string: str) -> Dataset:
        """Load pydicom dataset from json string

        There is a common gotcha in current pydicom (3.0.1) json support. This ignores
        file_meta completely as it is not mentioned in the DICOM standard JSON
        description. Annoyingly you do need parts of that information to interpret
        the image data in a dataset. Workaround here is to only support
        ExplicitVRLittleEndian
        """
        ds = Dataset.from_json(
            json_string, bulk_data_uri_handler=cls.bulk_data_reader
        )

        ds.file_meta = FileMetaDataset()
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

        return ds


class SampleDataset(BaseModel):
    """A DICOM dataset that can be used as a samples for testing and validation

    Extra features are original UID, PI regions, and possibility to replace image
    data with noise. Noise replaced image data will take only a fraction of the
    original data but retain the original shape.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)  # for Dataset

    uid: str
    dataset: Dataset
    pi_regions: List[PixelArea]

    def to_json(self, replace_pixel_data: bool = False) -> str:
        """Serialize to JSON, optionally replace pixel data"""
        data = json.loads(self.model_dump_json(exclude={"dataset"}))

        # Inject the custom dataset serialization
        data["dataset"] = json.loads(
            SampleDataSerializer().to_json(
                self.dataset, replace_with_pixel_noise=replace_pixel_data
            )
        )
        return json.dumps(data, indent=2)

    @field_serializer("dataset")
    def serialize_dataset(self, ds: Dataset) -> dict:
        """Serialize pydicom Dataset to a JSON-compatible dict."""
        return ds.to_json_dict()

    @field_validator("dataset", mode="before")
    @classmethod
    def deserialize_dataset(cls, v: Any) -> Dataset:
        """Deserialize a dict/string back into a pydicom Dataset."""
        if isinstance(v, Dataset):
            return v
        if isinstance(v, str):
            return SampleDataSerializer().to_dataset(v)
        if isinstance(v, dict):
            return SampleDataSerializer().to_dataset(json.dumps(v))
        raise ValueError(f"Cannot deserialize Dataset from type {type(v)}")

    def generate_reference(self) -> tuple[Dataset, Dataset]:
        """Returns original dataset and reference dataset where PI locations have
        been set to zero
        """
        return generate_reference(self)


def generate_reference(sample: SampleDataset) -> tuple[Dataset, Dataset]:
    """Generate an original - reference dataset pair from sample data set

    Converts the custom SampleDataset objects into a less custom format -
    just two pydicom datasets.

    Reads information from SampleDataset objects. These contain a dicom dataset and
    PI locations. For each SampleDataset, PILocationValidationSet returns dataset and
    creates a second dataset where the PI locations have been zeroed
    (set to pixel value 0)
    """
    reference = sample.dataset
    result = deepcopy_fix(sample.dataset)
    for pir in sample.pi_regions:
        # paint all PI regions zero in result
        result = add_blocks(
            result,
            [
                Block(
                    origin_x=pir.x,
                    origin_y=pir.y,
                    width=pir.width,
                    height=pir.height,
                )
            ],
            value=0,
        )
    return reference, result
