"""Creating and working with examples of DICOM datasets and dataset transformations"""
import numpy as np
from dicomgenerator.pixeldata import draw_noise
from pydicom import Dataset
from pydicom.tag import Tag

# Build SampleDataset from any dataset

# Pixeldata and replace PixelData with BulkURI random generator seed

# Show how to load such a dataset again


def get_pixel_dtype(ds: Dataset) -> np.dtype:
    """
    Infer the correct numpy dtype for the PixelData of a DICOM dataset.

    Relies on:
      - BitsAllocated  (0028,0100): storage width in bits (8, 16, 32, 64)
      - PixelRepresentation (0028,0103): 0 = unsigned, 1 = signed
    """
    bits = ds.BitsAllocated
    signed = ds.PixelRepresentation == 1  # 1 → signed, 0 → unsigned

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

    dtype = dtype_map.get((bits, signed))
    if dtype is None:
        raise ValueError(
            f"Unsupported BitsAllocated={bits}, "
            f"PixelRepresentation={ds.PixelRepresentation}"
        )

    return np.dtype(dtype)


PIXEL_DATA_TAGS = (Tag(0x7FE00010),)  # Pixel Data


def bulk_data_handler(data_element) -> str:
    """Return a dummy BulkDataURI for pixel data elements."""

    if data_element.tag in PIXEL_DATA_TAGS:
        return f"https://example.com/wado/pixeldata/{data_element.tag}"
    else:
        # cannot handle anything but pixel data at the moment
        return data_element.to_json()


def bulk_data_reader(tag, vr, bulk_data_uri):
    if tag in PIXEL_DATA_TAGS:
        value = draw_noise(201, 301, "uint8", seed=bulk_data_uri)
        return value.tobytes()
    else:
        return None
