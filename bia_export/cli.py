from pathlib import Path
import logging

import rich
import typer
from rich.logging import RichHandler

from bia_integrator_api import models as api_models

from .data_mapping_utils import (
    transform_ai_study_dict,
    transform_so_study_dict,
    transform_study_dict,
    create_export_image,
    get_ann_uuid_by_sourcename,
)

from .bia_client_utils import (
    rw_client,
    get_study_uuid_by_accession_id,
    get_images_with_a_rep_type,
    get_file_references_by_study_uuid,
    get_annotation_file_uuids_by_study_uuid,
    get_annotation_files_by_study_uuid,
    get_images_by_study_uuid,
)

from .config import settings
from .models import (
    ExportDataset,
    ExportAIDataset,
    ExportImage,
    Exports,
    AIExports,
    Link,
    ExportSODataset,
    SOExports,
)


logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger()

app = typer.Typer()


def bia_image_to_export_image(
    image: api_models.BIAImage, study: api_models.BIAStudy, use_cache=True
) -> ExportImage:

    output_dirpath = settings.cache_root_dirpath / "images"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{image.uuid}.json"

    if use_cache and output_fpath.exists():
        return ExportImage.parse_file(output_fpath)

    image_acquisitions = []
    specimens = []
    biosamples = []

    # image->image_acquisition is 1->many, though usually only 1 acquisition per image
    image_acquisitions.extend(
        [
            rw_client.get_image_acquisition(image_acquisition_uuid)
            for image_acquisition_uuid in image.image_acquisitions_uuid
        ]
    )

    # image->specimen should be 1->1, but have to assume 1->many because of 1->many image->image_acquisition link
    for image_acquisition in image_acquisitions:
        specimens.append(rw_client.get_specimen(image_acquisition.specimen_uuid))

    for specimen in specimens:
        biosamples.append(rw_client.get_biosample(specimen.biosample_uuid))

    converted_image = create_export_image(
        image, study, image_acquisitions, specimens, biosamples
    )

    with open(output_fpath, "w") as fh:
        fh.write(converted_image.json(indent=2))

    return converted_image


def fileref_to_export_annotations(fileref: api_models.FileReference, use_cache=True):

    output_dirpath = settings.cache_root_dirpath / "images"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{fileref.uuid}.json"

    if use_cache and output_fpath.exists():
        return ExportImage.parse_file(output_fpath)

    # FIXME - Write the proper export_ann
    export_ann = None

    if export_ann:
        with open(output_fpath, "w") as fh:
            fh.write(export_ann.json(indent=2))

    return export_ann


# FIXME - we get images twice...
def study_uuid_to_export_dataset(study_uuid) -> ExportDataset:

    output_dirpath = settings.cache_root_dirpath / "datasets"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{study_uuid}.json"
    if output_fpath.exists():
        return ExportDataset.parse_file(output_fpath)

    bia_study = rw_client.get_study(study_uuid, apply_annotations=True)

    images = get_images_with_a_rep_type(study_uuid, "ome_ngff")
    transform_dict = transform_study_dict(bia_study)
    transform_dict["image_uuids"] = [image.uuid for image in images]
    transform_dict["links"] = [
        Link(
            name="original_submission",
            type="original_submission",
            url=f"https://www.ebi.ac.uk/biostudies/BioImages/studies/{bia_study.accession_id}",
        )
    ]

    with open(output_fpath, "w") as fh:
        fh.write(ExportDataset(**transform_dict).json(indent=2))
        logger.info(f"Saved to {output_fpath}")

    return ExportDataset(**transform_dict)


# FIXME - we get images twice...
def study_uuid_to_export_sodataset(study_uuid: str) -> ExportSODataset:

    output_dirpath = settings.cache_root_dirpath / "datasets"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{study_uuid}.json"
    if output_fpath.exists():
        return ExportSODataset.parse_file(output_fpath)

    bia_study = rw_client.get_study(study_uuid, apply_annotations=True)

    images = get_images_with_a_rep_type(study_uuid, "ome_ngff")
    transform_dict = transform_so_study_dict(bia_study)
    transform_dict["image_uuids"] = [image.uuid for image in images]
    transform_dict["links"] = [
        Link(
            name="original_submission",
            type="original_submission",
            url=f"https://www.ebi.ac.uk/biostudies/BioImages/studies/{bia_study.accession_id}",
        )
    ]

    with open(output_fpath, "w") as fh:
        fh.write(ExportSODataset(**transform_dict).json(indent=2))

    return ExportSODataset(**transform_dict)


# FIXME - we get images twice...
def study_uuid_to_export_ai_dataset(study_uuid: str) -> ExportAIDataset:

    output_dirpath = settings.cache_root_dirpath / "datasets"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{study_uuid}.json"
    if output_fpath.exists():
        return ExportDataset.parse_file(output_fpath)

    bia_study = rw_client.get_study(study_uuid, apply_annotations=True)

    # Get OME-NGFF images only
    images = get_images_with_a_rep_type(study_uuid, "ome_ngff",limit=10)
    # Get all images
    n_images = bia_study.images_count
    study_images = get_images_by_study_uuid(study_uuid, limit=n_images)

    transform_dict = transform_ai_study_dict(bia_study)
    transform_dict["image_uuids"] = [image.uuid for image in images]
    transform_dict["links"] = [
        Link(
            name="original_submission",
            type="original_submission",
            url=f"https://www.ebi.ac.uk/biostudies/BioImages/studies/{bia_study.accession_id}",
        )
    ]
    transform_dict["annfile_uuids"] = get_annotation_file_uuids_by_study_uuid(
        study_uuid, limit=100
    )

    # Get all annotations
    # Assuming max = all file references
    n_filereferences = bia_study.file_references_count
    annotation_files = get_annotation_files_by_study_uuid(study_uuid, limit=n_filereferences)

    ann_uuids_by_sourcename = get_ann_uuid_by_sourcename(annotation_files)
    # rich.print(ann_uuids_by_sourcename)

    im_uuid_by_name = {image.name: image.uuid for image in study_images}

    # Find annotations that are also images
    annotation_images = { 
        annfile.uuid: im_uuid_by_name.get(annfile.name) 
        for annfile in annotation_files.values()
        if im_uuid_by_name.get(annfile.name)                                
    }
    # Find images that are not annotations
    nonannotation_images = [
        image for image in study_images if image.uuid not in annotation_images.values()
    ]

    transform_dict["annotation_images"] = annotation_images

    transform_dict["corresponding_source_im_ann_uuids"] = {
        image.uuid: ann_uuids_by_sourcename.get(image.name) for image in nonannotation_images
    }

    transform_dict["corresponding_ann_source_im_uuids"] = {
        annfile.uuid: im_uuid_by_name.get(annfile.attributes["source image"])
        for annfile in annotation_files.values()
    }



    with open(output_fpath, "w") as fh:
        fh.write(ExportAIDataset(**transform_dict).json(indent=2))

    return ExportAIDataset(**transform_dict)


def study_uuid_to_export_images(study_uuid: str) -> dict[str, ExportImage]:
    study = rw_client.get_study(study_uuid)
    images = get_images_with_a_rep_type(study_uuid, "ome_ngff", limit=500)

    return {image.uuid: bia_image_to_export_image(image, study) for image in images}


@app.command()
def show_export(accession_id: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)

    export_dataset = study_uuid_to_export_dataset(study_uuid)

    rich.print(export_dataset)


@app.command()
def show_so_export(accession_id: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)
    study = rw_client.get_study(study_uuid, apply_annotations=True)
    sodict = transform_so_study_dict(study)

    export_dataset = study_uuid_to_export_sodataset(study_uuid)

    # rich.print(api_study)
    # rich.print(sodict)
    rich.print(export_dataset)


@app.command()
def show_fileref_export(accession_id: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)
    rich.print(get_annotation_files_by_study_uuid(study_uuid))


@app.command()
def show_image_export(accession_id: str, image_uuid: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)
    study = rw_client.get_study(study_uuid, apply_annotations=True)
    image = rw_client.get_image(image_uuid, apply_annotations=True)
    export_image = bia_image_to_export_image(image, study, use_cache=False)
    rich.print(export_image)


@app.command()
def export_all_images(output_filename: Path = Path("bia-images-export.json")):

    accession_ids = [
        "S-BSST223",
        "S-BSST429",
        "S-BIAD144",
        "S-BIAD217",
        "S-BIAD368",
        "S-BIAD425",
        "S-BIAD570",
        "S-BIAD1009",
        "S-BIAD582",
        "S-BIAD606",
        "S-BIAD608",
        "S-BIAD620",
        "S-BIAD661",
        "S-BIAD626",
        "S-BIAD627",
        "S-BIAD725",
        "S-BIAD746",
        "S-BIAD826",
        "S-BIAD886",
        "S-BIAD901",
        "S-BIAD915",
        "S-BIAD916",
        "S-BIAD922",
        "S-BIAD928",
        "S-BIAD952",
        "S-BIAD954",
        "S-BIAD961",
        "S-BIAD963",
        "S-BIAD968",
        "S-BIAD976",
        "S-BIAD978",
        "S-BIAD987",
        "S-BIAD988",
        "S-BIAD993",
        "S-BIAD999",
        "S-BIAD1008",
        "S-BIAD1012",
        "S-BIAD1015",
        "S-BIAD1021",
        "S-BIAD1024",
        "S-BIAD531",
        "S-BIAD599",
        "S-BIAD463",
        "S-BIAD634",
        "S-BIAD686",
        "S-BIAD493",
    ]

    study_accession_ids_to_export = accession_ids
    study_uuids_by_accession_id = {
        accession_id: get_study_uuid_by_accession_id(accession_id)
        for accession_id in study_accession_ids_to_export
    }

    export_images = {}
    for study_uuid in study_uuids_by_accession_id.values():
        new_export_images = study_uuid_to_export_images(study_uuid)
        export_images.update(new_export_images)

    exports = Exports(images=export_images)

    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))


@app.command()
def export_defaults(output_filename: Path = Path("bia-export.json")):

    accession_ids = [
        "S-BSST223",
        "S-BSST429",
        "S-BIAD144",
        "S-BIAD217",
        "S-BIAD368",
        "S-BIAD425",
        "S-BIAD582",
        "S-BIAD606",
        "S-BIAD608",
        "S-BIAD620",
        "S-BIAD661",
        "S-BIAD626",
        "S-BIAD627",
        "S-BIAD725",
        "S-BIAD746",
        "S-BIAD826",
        "S-BIAD886",
        "S-BIAD901",
        "S-BIAD915",
        "S-BIAD916",
        "S-BIAD922",
        "S-BIAD928",
        "S-BIAD952",
        "S-BIAD954",
        "S-BIAD961",
        "S-BIAD963",
        "S-BIAD968",
        "S-BIAD976",
        "S-BIAD978",
        "S-BIAD987",
        "S-BIAD988",
        "S-BIAD993",
        "S-BIAD999",
        "S-BIAD1008",
    ]

    study_accession_ids_to_export = accession_ids

    study_uuids_by_accession_id = {
        accession_id: get_study_uuid_by_accession_id(accession_id)
        for accession_id in study_accession_ids_to_export
    }

    export_datasets = {
        accession_id: study_uuid_to_export_dataset(uuid)
        for accession_id, uuid in study_uuids_by_accession_id.items()
    }

    export_images = {}
    for study_uuid in study_uuids_by_accession_id.values():
        new_export_images = study_uuid_to_export_images(study_uuid)
        export_images.update(new_export_images)

    exports = Exports(datasets=export_datasets, images=export_images)

    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))


@app.command()
def ai_datasets(output_filename: Path = Path("bia-ai-export.json")):

    accession_ids = [
        "S-BIAD531",
        "S-BIAD599",
        "S-BIAD463",
        "S-BIAD634",
        "S-BIAD686",
        "S-BIAD493",
    ]

    study_accession_ids_to_export = accession_ids

    study_uuids_by_accession_id = {
        accession_id: get_study_uuid_by_accession_id(accession_id)
        for accession_id in study_accession_ids_to_export
    }

    export_datasets = {
        accession_id: study_uuid_to_export_ai_dataset(uuid)
        for accession_id, uuid in study_uuids_by_accession_id.items()
    }

    export_images = {}
    for study_uuid in study_uuids_by_accession_id.values():
        new_export_images = study_uuid_to_export_images(study_uuid)
        export_images.update(new_export_images)

    exports = AIExports(datasets=export_datasets, images=export_images)

    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))


@app.command()
def spatial_omics_datasets(
    output_filename: Path = Path("bia-spatialomics-export.json"),
):

    accession_ids = ["S-BIAD570", "S-BIAD1009"]

    study_accession_ids_to_export = accession_ids

    study_uuids_by_accession_id = {
        accession_id: get_study_uuid_by_accession_id(accession_id)
        for accession_id in study_accession_ids_to_export
    }

    export_datasets = {
        accession_id: study_uuid_to_export_sodataset(uuid)
        for accession_id, uuid in study_uuids_by_accession_id.items()
    }

    export_images = {}
    for study_uuid in study_uuids_by_accession_id.values():
        new_export_images = study_uuid_to_export_images(study_uuid)
        export_images.update(new_export_images)

    exports = SOExports(datasets=export_datasets, images=export_images)

    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))


@app.command()
def annotation_files(output_filename: Path = Path("bia-annotation_files.json")):

    accession_ids = [
        "S-BIAD531",
        "S-BIAD599",
        "S-BIAD463",
        "S-BIAD634",
        "S-BIAD686",
        "S-BIAD493",
    ]

    study_accession_ids_to_export = accession_ids

    study_uuids_by_accession_id = {
        accession_id: get_study_uuid_by_accession_id(accession_id)
        for accession_id in study_accession_ids_to_export
    }

    export_annotfiles = {}
    for study_uuid in study_uuids_by_accession_id.values():
        study_filerefs = get_file_references_by_study_uuid(study_uuid)
        export_filerefs = {
            fileref.uuid: fileref_to_export_annotations(fileref)
            for fileref in study_filerefs
        }
        export_annotfiles.update(export_filerefs)

    # FIXME - Write the proper export call
    exports = None
    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))


if __name__ == "__main__":
    app()
