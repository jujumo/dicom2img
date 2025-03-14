import pydicom
import csv
from jsonargparse import CLI
from typing import List
from rich.progress import track
from dataclasses import dataclass, fields, asdict
import os.path as path
from dicom2img.dicom import dicom2file


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


def records2images(
        dicom_dirpath: str,
        images_dirpath: str,
        records: List[DicomdirRecord],
        image_format: str = '.png'
):
    for record in track(records):
        dicom_filepath = path.join(dicom_dirpath, *record.referenced_file_id)
        image_filepath = path.join(images_dirpath, record.referenced_file_id[-1] + image_format)
        dicom2file(dicom_filepath, image_filepath)


def dicomdir2files(
        dicomdir_filepath: str,
        output_dirpath: str,
        image_format: str = '.npy'
):
    records = dicomdir2records(dicomdir_filepath)
    csv_filepath = path.join(output_dirpath, 'index.csv')
    records2csv(csv_filepath=csv_filepath, records=records)
    dicom_dirpath = path.dirname(dicomdir_filepath)
    images_dirpath = path.join(output_dirpath, 'images')
    records2images(dicom_dirpath=dicom_dirpath, images_dirpath=images_dirpath,
                   records=records, image_format=image_format)


def dicomdir_cli():
    CLI(dicomdir2files)


if __name__ == '__main__':
    dicomdir_cli()

