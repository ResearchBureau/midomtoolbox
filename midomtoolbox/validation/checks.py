"""Ways to compare a deidentified dataset to an original + reference result"""

from midom.validation import Check, ValidationFailedError
from pydicom import Dataset


class BurntInInfoRemovedCheck(Check):
    description = "Checks whether the correct pixels have been blacked out"

    def __init__(self, black_out_value=0):
        self.black_out_value = 0

    def run(self, original: Dataset, reference: Dataset, result: Dataset):
        """Check whether result conforms to the reference result

        Raises
        ------
        ValidationFailedError
            If result does not conform.
        """

        raise ValidationFailedError("Not implemented yet!")
