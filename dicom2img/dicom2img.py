import pydicom
import numpy as np
import os
import os.path as path
from jsonargparse import CLI
from typing import Optional


def load_dicom_series(directory):
    """
    Load a series of DICOM images from a directory and convert them to a NumPy voxel grid.

    Parameters:
    - directory: str, path to the directory containing DICOM files.

    Returns:
    - voxel_grid: numpy.ndarray, 3D array representing the voxel grid.
    """
    # List all DICOM files in the directory
    dicom_files = [f for f in os.listdir(directory) if f.startswith('IM')]
    # Sort files to ensure they are in the correct order
    dicom_files.sort()
    dicom_paths = [os.path.join(directory, f) for f in dicom_files]
    image_files = []
    for dicom_path in dicom_paths:
        dicom_image = pydicom.dcmread(dicom_path)
        if hasattr(dicom_image, 'pixel_array'):
            image_files.append(dicom_image)

    return image_files


def dicom2img():
    pass

def dicom2img_cli():
    CLI(dicom2img)


if __name__ == '__main__':
    dicom2img_cli()

