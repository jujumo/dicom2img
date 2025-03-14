import pydicom
from jsonargparse import CLI
from PIL import Image
import numpy as np
from typing import Optional
import os.path as path


IMG_EXT = ['.jpeg', '.jpg', '.png']


def dicom2np(
        dicom_filepath: str
):
    dicom_file = pydicom.dcmread(dicom_filepath)
    return dicom_file.pixel_array


def dicom2img(
        dicom_filepath: str,
):
    arr = dicom2np(dicom_filepath)
    if arr is None:
        return
    img = Image.fromarray(arr)
    return img


def dicom2file(
        dicom_filepath: str,
        output_filepath: Optional[str]
):
    if output_filepath is None:
        output_filepath = path.splitext(dicom_filepath)[0] + '.png'
    arr = dicom2np(dicom_filepath)
    out_ext = path.splitext(output_filepath)[1].lower()
    if out_ext == '.npy':
        np.save(output_filepath, arr)
    if out_ext in IMG_EXT:
        img = Image.fromarray(arr)
        img.save(output_filepath)


def dicom_cli():
    CLI(dicom2file)


if __name__ == '__main__':
    dicom_cli()

