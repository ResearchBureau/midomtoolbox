import pytest
from pydantic import ValidationError
from pydicom import examples


from midomtoolbox.validation.sampling import (
    PixelNoiseURI,
    SampleDataSerializer,
)


def test_pixel_data_replace():

    serializer = SampleDataSerializer()

    # a dataset with actual pixeldata
    ds = examples.ct

    # persist this dataset. Pixeldata will be saved as PixelNoiseURI
    json_data = serializer.to_json(ds)

    # load again, PixelNoiseURI is translated to actual noise
    loaded = serializer.to_dataset(json_data)

    # persist/load -> check still the same
    # for debug
    # import matplotlib.pyplot as plt
    # plt.imshow(loaded.pixel_array)
    # plt.show()
    # plt.imshow(ds.pixel_array)
    # plt.show()

    assert ds
    assert loaded


@pytest.mark.parametrize(
    "uri,exp_height,exp_width,exp_bit_depth,exp_seed",
    [
        ("pixelnoise://100/300/uint8/aseed", 100, 300, "uint8", "aseed"),
        ("pixelnoise://1/1/float32/xyz", 1, 1, "float32", "xyz"),
        (
            "pixelnoise://1920/1080/uint16/my-seed",
            1920,
            1080,
            "uint16",
            "my-seed",
        ),
        ("pixelnoise://0/0/uint8/empty", 0, 0, "uint8", "empty"),
    ],
)
def test_from_string_valid(
    uri, exp_height, exp_width, exp_bit_depth, exp_seed
):
    result = PixelNoiseURI.from_string(uri)
    assert result.height == exp_height
    assert result.width == exp_width
    assert result.bit_depth == exp_bit_depth
    assert result.seed == exp_seed


@pytest.mark.parametrize(
    "uri",
    [
        "noise://100/300/uint8/aseed",  # wrong scheme
        "pixelnoise://100/300/uint8",  # too few parts
        "pixelnoise://100/300/uint8/s/extra",  # too many parts
        "pixelnoise://abc/300/uint8/aseed",  # non-integer height
        "pixelnoise://100/xyz/uint8/aseed",  # non-integer width
        "100/300/uint8/aseed",  # missing scheme entirely
        "",  # empty string
    ],
)
def test_from_string_invalid(uri):
    with pytest.raises((ValueError, ValidationError)):
        PixelNoiseURI.from_string(uri)


@pytest.mark.parametrize(
    "exp_uri,height,width,bit_depth,seed",
    [
        ("pixelnoise://100/300/uint8/aseed", 100, 300, "uint8", "aseed"),
        ("pixelnoise://1/1/float32/xyz", 1, 1, "float32", "xyz"),
        (
            "pixelnoise://1920/1080/uint16/my-seed",
            1920,
            1080,
            "uint16",
            "my-seed",
        ),
        ("pixelnoise://0/0/uint8/empty", 0, 0, "uint8", "empty"),
    ],
)
def test_to_string(exp_uri, height, width, bit_depth, seed):
    uri = PixelNoiseURI(
        height=height, width=width, bit_depth=bit_depth, seed=seed
    )
    assert uri.to_string() == exp_uri


@pytest.mark.parametrize(
    "uri",
    [
        "pixelnoise://100/300/uint8/aseed",
        "pixelnoise://1/1/float32/xyz",
        "pixelnoise://1920/1080/uint16/my-seed",
    ],
)
def test_round_trip(uri):
    assert PixelNoiseURI.from_string(uri).to_string() == uri
