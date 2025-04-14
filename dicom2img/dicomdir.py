import os

import matplotlib.pyplot as plt
import numpy as np
import pydicom
import csv
from enum import Enum
from jsonargparse import CLI
from typing import List
from rich.progress import track
from dataclasses import dataclass, fields, asdict
import os.path as path
from dicom2img.dicom import dicom2np, np2img, ImageType, IMAGE_EXT


@dataclass
class DicomdirRecord:
    patient_id: str
    patient_name: str
    study_date: str
    study_id: str
    study_description: str
    series_number: int
    modality: str
    instance_number: int
    referenced_file_id: List[str]


DICOMDIR_KEYS = [field.name for field in fields(DicomdirRecord)]


def dicomdir2records(
        dicomdir_filepath: str
):
    records = []
    dicomdir_file = pydicom.dcmread(dicomdir_filepath)
    for record in track(dicomdir_file.DirectoryRecordSequence):
        if not hasattr(record, 'DirectoryRecordType'):
            continue
        record_type = record.DirectoryRecordType
        if record_type == 'PATIENT':
            patient_id = record.PatientID
            patient_name = record.PatientName
        elif record_type == 'STUDY':
            study_date = record.StudyDate
            study_id = record.StudyID
            study_description = record.StudyDescription
        elif record_type == 'SERIES':
            series_number = record.SeriesNumber
            modality = record.Modality
        elif record_type == 'IMAGE':
            instance_number = record.InstanceNumber
            referenced_file_id = record.ReferencedFileID
            record = DicomdirRecord(patient_id, patient_name, study_date, study_id,
                             study_description, series_number, modality, instance_number, referenced_file_id)
            records.append(record)
    return records


def records2csv(
        csv_filepath: str,
        records: List[DicomdirRecord]
):
    with open(csv_filepath, mode='w', newline='') as out_file:
        csv_writer = csv.DictWriter(out_file, DICOMDIR_KEYS)
        # Write the header
        csv_writer.writeheader()
        for record in track(records):
            csv_writer.writerow(asdict(record))


def records2layers(
        dicom_root_dirpath: str,
        records: List[DicomdirRecord]
):
    """
    Is a generator function, giving an iterator over image layers
    """
    for record in records:
        dicom_filepath = path.join(dicom_root_dirpath, *record.referenced_file_id)
        arr = dicom2np(dicom_filepath)
        yield record, arr


def dicomdir2files(
        dicomdir_filepath: str,
        output_dirpath: str,
        itype: ImageType = ImageType.PNG,
        gain: float = 1.0,
        verbose: bool = False
):
    """
    Convert a DICOMDIR file and adjacent images files to a series of images.
    DICOMDIR file contains (relative) path to images. So, images must also be present while converting.
    :param dicomdir_filepath: input path to the DICOMDIR file.
    :param output_dirpath: output path, where to save exported images.
    :param itype: type of the output export image: png or numpy npy.
    :param gain: gain to apply to values [1] means no gain. -1 means auto gain.
    """

    os.makedirs(output_dirpath, exist_ok=True)

    # parse the DICOMDIR file, to make a register of the images.
    records = dicomdir2records(dicomdir_filepath)
    # save that register in a csv
    csv_filepath = path.join(output_dirpath, 'index.csv')
    records2csv(csv_filepath=csv_filepath, records=records)
    # convert the actual image files
    dicom_root_dirpath = path.dirname(dicomdir_filepath)
    layers = records2layers(dicom_root_dirpath=dicom_root_dirpath, records=records)

    # form images, save each layer individually in an image file.
    file_ext = IMAGE_EXT[itype]
    if itype in [ImageType.PNG, ImageType.JPG]:
        for record, arr in track(layers, total=len(records)):
            image_filename = f'{record.series_number:03}_{record.instance_number:05}_{record.referenced_file_id[-1]}' + file_ext
            image_filepath = path.join(output_dirpath, image_filename)
            img = np2img(arr, itype=itype, gain=gain)
            img.save(image_filepath)

    # for npy, aggregate sequences into voxel grid
    if itype in [ImageType.NPY]:
        # regroup voxel grid per sequence id
        sequences = {record.series_number: [] for record in records}
        for record, arr in track(layers, total=len(records)):
            seq_id = record.series_number
            sequences[seq_id].append(arr)
        # then save each voxel grid
        for seq_id, sequence in sequences.items():
            try:
                voxel_grid = np.stack(sequence, axis=2)
                voxel_filename = f'{seq_id:03}' + file_ext
                voxel_filepath = path.join(output_dirpath, voxel_filename)
                np.save(voxel_filepath, voxel_grid)
            except Exception as e:
                print(f'{e=}')

def dicomdir_cli():
    CLI(dicomdir2files)


if __name__ == '__main__':
    dicomdir_cli()

