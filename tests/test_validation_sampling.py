from pydicom import Dataset, examples

from midomtoolbox.validation.sampling import (
    bulk_data_handler,
    bulk_data_reader,
)


def test_pixel_data_replace():
    # a dataset with actual pixeldata
    ds = examples.ct

    # create SampleDataSerializer (or just load? Not sure)

    # persist this dataset

    # Check no pixeldata

    # load dataset

    # check that now noise pixeldata

    # persist/load -> check still the same

    # import matplotlib.pyplot as plt
    # plt.imshow(ds.pixel_array)
    # plt.show()

    json_data = ds.to_json(bulk_data_element_handler=bulk_data_handler)

    ds = Dataset.from_json(json_data, bulk_data_uri_handler=bulk_data_reader)
    assert ds

    # Pixeldata and replace PixelData with BulkURI random generator seed

    # Show how to load such a dataset again
