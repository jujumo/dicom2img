import pydicom
from jsonargparse import CLI
from PIL import Image
import numpy as np
from typing import Optional
import os.path as path
from enum import Enum


class ImageType(Enum):
    NPY = 0
    PNG = 1
    JPG = 3


IMAGE_EXT = {
    ImageType.NPY: '.npy',
    ImageType.PNG: '.png',
    ImageType.JPG: '.jpg',
}

EXT2TYPE = {v: k for k, v in IMAGE_EXT.items()}

IMAGE_DTYPE = {
    ImageType.NPY: np.uint16,
    ImageType.PNG: np.uint16,
    ImageType.JPG: np.uint8,
}


def dicom2np(
        dicom_filepath: str
):
    """ converts a dicom file to a numpy array """
    dicom_file = pydicom.dcmread(dicom_filepath)
    arr = dicom_file.pixel_array
    return arr


def np2img(
        arr: np.ndarray,
        itype: ImageType = ImageType.PNG,
        normalize: bool = False
):
    """ converts the numpy layer to an image, given the file format and depth. """
    # expect an array with uint12b coded on a uint16b
    dtype = IMAGE_DTYPE[itype]
    # for visualization, normalize
    if normalize:
        arr = arr.astype(np.uint32) * np.iinfo(dtype).max // np.max(arr)
        arr = arr.astype(dtype)
    # then convert to the proper data type
    if arr.dtype != dtype:
        in_max = np.iinfo(arr.dtype).max
        out_max = np.iinfo(dtype).max
        arr = arr.astype(dtype) * in_max / out_max
    img = Image.fromarray(arr)
    return img


def dicom2img(
        dicom_filepath: str,
        itype: ImageType = ImageType.PNG,
        normalize: bool = False
):
    """ converts the dicom image to a standard image file, given the file format and depth. """
    arr = dicom2np(dicom_filepath)
    img = np2img(arr, itype, normalize=normalize)
    return img


def dicom2file(
        dicom_filepath: str,
        image_filepath: Optional[str],
        normalize: bool = False,
        verbose: bool = True
):
    """ automatically converts the dicom image to either numpy or image file. """
    if image_filepath is None:
        image_filepath = path.splitext(dicom_filepath)[0] + '.png'
    arr = dicom2np(dicom_filepath)
    out_ext = path.splitext(image_filepath)[1].lower()
    itype = EXT2TYPE[out_ext]
    if itype == ImageType.NPY:
        np.save(image_filepath, arr)
    if itype != ImageType.NPY:
        # force normalisation for jpeg image
        if itype == ImageType.JPG:
            normalize = True
        img = np2img(arr, itype=itype, normalize=normalize)
        img.save(image_filepath)


def dicom_cli():
    CLI(dicom2file)


if __name__ == '__main__':
    dicom_cli()

