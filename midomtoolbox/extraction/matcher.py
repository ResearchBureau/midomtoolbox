import re

from pydicom.datadict import keyword_dict


def _normalize(s: str) -> str:
    """Lowercase, strip non-alphanumeric chars so spacing/casing/underscores don't
    matter.
    """
    return re.sub(r"[^a-z0-9]", "", s.lower())


# Build lookup table once
_NORM_TO_KEYWORD = {_normalize(kw): kw for kw in keyword_dict}


def find_dicom_keyword(query: str) -> str:
    """
    Match a free-text string to a DICOM element keyword by normalized
    (case/space/underscore-insensitive) exact match.

    Parameters
    ----------
    query : str
        e.g. "series description", "Series_Description"

    Returns
    -------
    str
        the matching keyword, or '' if no match is found
    """
    return _NORM_TO_KEYWORD.get(_normalize(query), "")
