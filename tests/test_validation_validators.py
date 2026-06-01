from dicomgenerator.generators import quick_dataset
from dicomgenerator.pixeldata import draw_noise
from midom.components import PixelArea

from midomtoolbox.validation.sampling import SampleDataset
from midomtoolbox.validation.validators import PILocationValidationSet


def test_pi_location_validation_set():
    sample1 = SampleDataset(
        uid="vna/1234/554/111",
        dataset=quick_dataset(
            Modality="CT",
            AccessionNumber="1234",
            PixelData=draw_noise(201, 301, "uint8"),
        ),
        pi_regions=[PixelArea(x=10, y=8, width=100, height=40)],
    )
    sample2 = SampleDataset(
        uid="vna/1234/554/444",
        dataset=quick_dataset(
            Modality="CT",
            AccessionNumber="5555",
            PixelData=draw_noise(201, 301, "uint8"),
        ),
        pi_regions=[PixelArea(x=4, y=20, width=30, height=50)],
    )

    pi_set = PILocationValidationSet(samples=[sample1, sample2])

    items = [x for x in pi_set.items()]
    assert items[0][0] != items[0][1]  # weak but enough for now.

    # for debug
    # import matplotlib.pyplot as plt
    # plt.imshow(items[1][0].pixel_array)
    # plt.show()
    # plt.imshow(items[1][1].pixel_array)
    # plt.show()
