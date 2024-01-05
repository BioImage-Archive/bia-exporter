from pathlib import Path
from typing import Dict

import rich
import typer

from .scli import rw_client, get_study_uuid_by_accession_id, get_images_with_a_rep_type
from .config import settings
from .models import ExportDataset, ExportImage, Exports, Link
from .proxyimage import ome_zarr_image_from_ome_zarr_uri

ITK_BASE="https://kitware.github.io/itk-vtk-viewer/app/?fileToLoad="
VIZARR_BASE="https://uk1s3.embassy.ebi.ac.uk/bia-zarr-test/vizarr/index.html?source="


app = typer.Typer()


def filter_image_attributes(image) -> Dict[str, str]:
    """Given a BIA Image, filter the attributes for those we wish to export
    and return as dict."""

    def filter_func(key):
        if key == "channels": return False
        if "channel" in key.lower():
            return True
        
        return False
        
    return {
        key: value
        for key, value in image.attributes.items()
        if filter_func(key)
    }


def transform_study_dict(bia_study):
    keys = [
        'accession_id',
        'title',
        'release_date',
        'example_image_uri',
        'imaging_type',
        'organism'
    ]
    base_dict = {
        key: bia_study.__dict__[key]
        for key in keys
    }

    base_dict['n_images'] = bia_study.images_count

    return base_dict


def transform(bia_study):
    keys = [
        'accession_id',
        'title',
        'release_date',
        'example_image_uri',
        'imaging_type',
        'organism'
    ]
    base_dict = {
        key: bia_study.__dict__[key]
        for key in keys
    }

    base_dict['n_images'] = bia_study.images_count

    return base_dict


def bia_image_to_export_image(image, study):

    output_dirpath = settings.cache_root_dirpath / "images"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{image.uuid}.json"
    if output_fpath.exists():
        return ExportImage.parse_file(output_fpath)
    
    reps_by_type = {
        rep.type: rep
        for rep in image.representations
    }

    ome_zarr_uri = reps_by_type["ome_ngff"].uri[0]
    im = ome_zarr_image_from_ome_zarr_uri(ome_zarr_uri)

    try:
        thumbnail_uri=reps_by_type["thumbnail"].uri[0]
    except KeyError:
        thumbnail_uri = ""

    export_im = ExportImage(
        uuid=image.uuid,
        name=Path(image.name).name,
        alias="IM1",
        original_relpath=image.original_relpath,
        thumbnail_uri=thumbnail_uri,
        study_accession_id=study.accession_id,
        study_title=study.title,
        release_date=study.release_date,
        itk_uri=ITK_BASE + reps_by_type["ome_ngff"].uri[0],
        vizarr_uri=VIZARR_BASE + reps_by_type["ome_ngff"].uri[0],
        sizeX=im.sizeX,
        sizeY=im.sizeY,
        sizeZ=im.sizeZ,
        sizeT=im.sizeT,
        sizeC=im.sizeC,
        PhysicalSizeX=im.PhysicalSizeX,
        PhysicalSizeY=im.PhysicalSizeY,
        PhysicalSizeZ=im.PhysicalSizeZ,
        attributes=filter_image_attributes(image)
    )

    with open(output_fpath, "w") as fh:
        fh.write(export_im.json(indent=2))

    return export_im


# FIXME - we get images twice...
def study_uuid_to_export_dataset(study_uuid) -> ExportDataset:

    output_dirpath = settings.cache_root_dirpath / "datasets"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{study_uuid}.json"
    if output_fpath.exists():
        return ExportDataset.parse_file(output_fpath)

    bia_study = rw_client.get_study(study_uuid)

    images = get_images_with_a_rep_type(study_uuid, "ome_ngff")
    transform_dict = transform_study_dict(bia_study)
    rich.print(transform_dict)
    transform_dict["image_uuids"] = [image.uuid for image in images]
    transform_dict["links"] = [
        Link(
            name="original_submission",
            type="original_submission",
            url=f"https://www.ebi.ac.uk/biostudies/BioImages/studies/{bia_study.accession_id}"
        )
    ]

    with open(output_fpath, "w") as fh:
        fh.write(ExportDataset(**transform_dict).json(indent=2))

    return ExportDataset(**transform_dict)


def study_uuid_to_export_images(study_uuid):
    study = rw_client.get_study(study_uuid)
    images = get_images_with_a_rep_type(study_uuid, "ome_ngff")
    
    return {image.uuid: bia_image_to_export_image(image, study) for image in images}


@app.command()
def show_export(accession_id: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)
    api_study = rw_client.get_study(study_uuid)

    export_dataset = study_uuid_to_export_dataset(study_uuid)

    # rich.print(api_study)
    # rich.print(export_dataset)


@app.command()
def export_defaults(output_filename: Path = Path("bia-export.json")):

    accession_ids = [
        "S-BIAD144", "S-BIAD217", "S-BIAD368", "S-BIAD425", "S-BIAD582", "S-BIAD606",
        "S-BIAD608", "S-BIAD620", "S-BIAD661", "S-BIAD626",
        "S-BIAD627", "S-BIAD916", "S-BIAD952", "S-BIAD961", "S-BIAD963", "S-BIAD968"
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

    exports = Exports(
        datasets=export_datasets,
        images=export_images
    )

    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))


if __name__ == "__main__":
    app()