"""Useful code for debugging pixeldata handling"""
from typing import Union

import matplotlib.pyplot as plt
from numpy import ndarray
from pydicom.dataset import Dataset


def display_dicom_images(elements: dict[str, Union[Dataset, ndarray]]) -> None:
    """
    Display DICOM images side by side using matplotlib.

    Parameters
    ----------
    elements : dict[str, Union[Dataset,ndarray]]
        Mapping of display titles to pydicom Dataset objects or numpy ndarray.
    """
    fig = create_figure(elements)
    fig.show()


def create_figure(elements: dict[str, Union[Dataset, ndarray]]):
    fig, axes = plt.subplots(1, len(elements), figsize=(5 * len(elements), 5))

    if len(elements) == 1:
        axes = [axes]

    for ax, (title, element) in zip(axes, elements.items()):
        try:
            pixel_array = element.pixel_array
        except AttributeError:
            pixel_array = element

        ax.imshow(pixel_array, cmap="gray")
        ax.set_title(title, fontsize=14)
        ax.axis("off")

    return fig
