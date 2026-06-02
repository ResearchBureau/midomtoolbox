from typing import Iterator, List, Tuple, Union

from midom.validation import DatasetRejected, ValidationSet
from pydicom import Dataset

from midomtoolbox.validation.sampling import SampleDataset, generate_reference


class PILocationValidationSet(ValidationSet):
    """A validation set that yields pairs of original -> original with zeroed boxes at
    locations of PI. For training and validating pixel cleaning specifically.

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
            reference, result = generate_reference(sample)
            yield reference, result
