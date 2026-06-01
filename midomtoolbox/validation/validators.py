from typing import Iterator, List, Tuple, Union

from dicomgenerator.pixeldata import Block, add_blocks
from midom.validation import DatasetRejected, ValidationSet, deepcopy_fix
from pydicom import Dataset

from midomtoolbox.validation.sampling import SampleDataset


class PILocationValidationSet(ValidationSet):
    """A validation set that yields pairs of original -> original with black boxes at
    locations of PI. For training and validating pixel cleaning specifically.

    Reads information from SampleDataset objects. These contain a dicom dataset and
    PI locations. For each SampleDataset, PILocationValidationSet returns dataset and
    creates a second dataset where the PI locations have been removed
    (set to pixel value 0)
    """

    samples: List[SampleDataset]  # all samples to return

    def items(
        self,
    ) -> Iterator[Tuple[Dataset, Union[DatasetRejected, Dataset]]]:
        """Yields pairs of (dataset -> correct deidentification result example)

        Returns
        -------
        Tuple[Dataset, Dataset]
            If the example dataset should be deidentified

        Tuple[Dataset, DatasetRejected]
            If the correct response should be to reject the example dataset

        """
        for sample in self.samples:
            reference = sample.dataset
            result = deepcopy_fix(sample.dataset)
            for pir in sample.pi_regions:
                # paint all PI regions black in result
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
            yield reference, result
