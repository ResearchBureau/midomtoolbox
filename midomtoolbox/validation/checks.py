"""Ways to compare a deidentified dataset to an original + reference result"""
import os
import tempfile
from pathlib import Path


import numpy as np
from midom.validation import Check, ValidationFailedError
from pydicom import Dataset

from midomtoolbox.logs import get_module_logger
from midomtoolbox.pixel_data import create_figure

logger = get_module_logger("checks")


class BurntInInfoRemovedCheck(Check):
    description = "Checks whether the correct pixels have been set to zero"

    def __init__(self, zero_out_value=0):
        self.zero_out_value = zero_out_value

    def run(self, original: Dataset, reference: Dataset, result: Dataset):
        """Check whether all pixels that were removed in reference were also removed
        in result. Note that this check passes if the result removes more pixels than
        the reference. So in principle a fully removed result (all zero) always
        passes. There are probably better ways to test but this is enough for now.

        Raises
        ------
        ValidationFailedError
            If result does not conform.
        """
        # look at difference between original and reference. What has been zeroed out?
        # Have the same areas been zeroed out in result?

        # check every place where the reference image is 0. This includes
        # all zeroed-out areas. I might also include original pixels
        # that just happen to have the same value. I don't really see a way
        # around this if we want to compare image data only, without relying
        # on external information
        mask = reference.pixel_array == self.zero_out_value
        masked_difference = np.where(
            mask, reference.pixel_array - result.pixel_array, 0
        )

        if os.getenv("WRITE_BURNT_IN_DEBUG_IMAGE") in {"TRUE", "true", "1"}:
            temp_file_name = (
                Path(tempfile.gettempdir()) / "burnt_in_info_comparison.jpg"
            )
            logger.info(
                "WRITE_BURNT_IN_DEBUG_IMAGE was true in env. Writing debug "
                f"image to {temp_file_name}"
            )

            fig = create_figure(
                {
                    "original": original,
                    "reference": reference,
                    "result": result,
                    "difference": masked_difference,
                }
            )

            fig.savefig(temp_file_name)

        # If any area was zero in the reference image, and is not
        # zero in the result image, then something has not been properly
        # zeroed out. Validation should fail then.
        if not np.all(masked_difference == 0):
            total = masked_difference.size
            nonzero = np.count_nonzero(masked_difference)
            percentage = (nonzero / total) * 100

            raise ValidationFailedError(
                f"{nonzero} PI-containing pixels were not removed in "
                f"result ({percentage:.2f}% of total)"
            )
