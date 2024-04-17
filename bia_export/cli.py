from pathlib import Path
from typing import Dict
import logging

import rich
import typer
from rich.logging import RichHandler

logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger()

from .scli import (rw_client, get_study_uuid_by_accession_id, get_images_with_a_rep_type, 
                   get_file_references_by_study_uuid,
                   get_annotation_file_uuids_by_study_uuid,
                   get_image_by_accession_id_and_relpath)
from .config import settings
from .models import ExportDataset, ExportAIDataset, ExportImage, Exports, AIExports, Link, ExportSODataset, SOExports
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

def transform_ai_study_dict(bia_study):
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

    keys2 = [
        'example_annotation_uri',
        'annotation_type',
        'annotation_method',
        'models_description',
        'models_uri'
    ]
    base_dict.update({
        key: bia_study.attributes.get(key)
        for key in keys2
    })

    base_dict['n_images'] = bia_study.images_count

    return base_dict

def transform_so_study_dict(bia_study):
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

    keys2 = [
        # 'example_annotation_uri',
        # 'annotation_type',
        # 'annotation_method',
        # 'models_description',
        # 'models_uri',
        'scseq_desc',
        'scseq_link',
        'code_desc',
        'code_link'

    ]
    base_dict.update({
        key: bia_study.attributes.get(key)
        for key in keys2
    })

    base_dict['n_images'] = bia_study.images_count

    return base_dict

def bia_image_to_export_image(image, study, use_cache=True):

    output_dirpath = settings.cache_root_dirpath / "images"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{image.uuid}.json"

    if use_cache and output_fpath.exists():
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

    # FIXME - should generalise this
    source_image_uuid = image.attributes.get("source_image_uuid", None)
    source_image_thumbnail_uri = image.attributes.get("source_image_thumbnail_uri", None)
    overlay_image_uri = image.attributes.get("overlay_image_uri", None)

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
        source_image_uuid=source_image_uuid,
        source_image_thumbnail_uri=source_image_thumbnail_uri,
        overlay_image_uri=overlay_image_uri,

        attributes=filter_image_attributes(image)
    )




    # TODO: Refactor so titles and child uuids obtained in same API call - use for loop
    # Get BioSample, Specimen and ImageAcquisition
    specimen_uuids = []
    specimen_uuids.extend([rw_client.get_image_acquisition(image_acquisition_method_uuid).specimen_uuid for image_acquisition_method_uuid in image.image_acquisition_methods_uuid])

    biosample_uuids = []
    biosample_uuids.extend([rw_client.get_specimen(specimen_uuid).biosample_uuid for specimen_uuid in specimen_uuids])
    
    if len(image.image_acquisition_methods_uuid) > 0:
        image_acquisition = rw_client.get_image_acquisition(image.image_acquisition_methods_uuid[0])
        export_im.image_acquisition_title = image_acquisition.title
        export_im.image_acquisition_imaging_instrument = image_acquisition.imaging_instrument
        export_im.image_acquisition_image_acquisition_parameters = image_acquisition.image_acquisition_parameters
        export_im.image_acquisition_imaging_method = image_acquisition.imaging_method
    
    if len(specimen_uuids) > 0:
        specimen = rw_client.get_specimen(specimen_uuids[0])
        export_im.specimen_title = specimen.title
        export_im.specimen_sample_preparation_protocol = specimen.sample_preparation_protocol
        export_im.specimen_growth_protocol = specimen.growth_protocol

    if len(biosample_uuids) > 0:
        biosample = rw_client.get_biosample(biosample_uuids[0]).__dict__
        export_im.biosample_title = biosample["title"]
        export_im.biosample_organism_scientific_name = biosample["organism_scientific_name"]
        export_im.biosample_organism_common_name = biosample["organism_common_name"]
        export_im.biosample_organism_ncbi_taxon = biosample["organism_ncbi_taxon"]
        export_im.biosample_description = biosample["description"]
        export_im.biosample_biological_entity = biosample["biological_entity"]
        export_im.biosample_experimental_variables = ", ".join(biosample["experimental_variables"])
        export_im.biosample_extrinsic_variables = ", ".join(biosample["extrinsic_variables"])
        export_im.biosample_intrinsic_variables = ", ".join(biosample["intrinsic_variables"])

    with open(output_fpath, "w") as fh:
        fh.write(export_im.json(indent=2))

    return export_im

def fileref_to_export_annotations(fileref, use_cache=True):

    output_dirpath = settings.cache_root_dirpath / "images"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{fileref.uuid}.json"

    if use_cache and output_fpath.exists():
        return ExportImage.parse_file(output_fpath)
    
    # reps_by_type = {
    #     rep.type: rep
    #     for rep in image.representations
    # }

    # ome_zarr_uri = reps_by_type["ome_ngff"].uri[0]
    # im = ome_zarr_image_from_ome_zarr_uri(ome_zarr_uri)

    # try:
    #     thumbnail_uri=reps_by_type["thumbnail"].uri[0]
    # except KeyError:
    #     thumbnail_uri = ""

    # FIXME - should generalise this
    # source_image_uuid = image.attributes.get("source_image_uuid", None)
    # source_image_thumbnail_uri = image.attributes.get("source_image_thumbnail_uri", None)
    # overlay_image_uri = image.attributes.get("overlay_image_uri", None)

    # export_ann = ExportAnnotationFile(
    #     uuid=fileref.uuid,
    #     name=Path(fileref.name).name,
    #     alias=fileref.attributes.get("alias"),
    #     thumbnail_uri=thumbnail_uri,
    #     study_accession_id=study.accession_id,
    #     study_title=study.title,
    #     release_date=study.release_date,
    #     itk_uri=ITK_BASE + reps_by_type["ome_ngff"].uri[0],
    #     vizarr_uri=VIZARR_BASE + reps_by_type["ome_ngff"].uri[0],
    #     sizeX=im.sizeX,
    #     sizeY=im.sizeY,
    #     sizeZ=im.sizeZ,
    #     sizeT=im.sizeT,
    #     sizeC=im.sizeC,
    #     PhysicalSizeX=im.PhysicalSizeX,
    #     PhysicalSizeY=im.PhysicalSizeY,
    #     PhysicalSizeZ=im.PhysicalSizeZ,
    #     source_image_uuid=source_image_uuid,
    #     source_image_thumbnail_uri=source_image_thumbnail_uri,
    #     overlay_image_uri=overlay_image_uri,
    #     attributes=filter_image_attributes(image)
    # )

    # FIXME - Write the proper export_ann 
    export_ann = None

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
            url=f"https://www.ebi.ac.uk/biostudies/BioImages/studies/{bia_study.accession_id}"
        )
    ]

    with open(output_fpath, "w") as fh:
        fh.write(ExportDataset(**transform_dict).json(indent=2))
        logger.info(f"Saved to {output_fpath}")

    return ExportDataset(**transform_dict)

# FIXME - we get images twice...
def study_uuid_to_export_sodataset(study_uuid) -> ExportSODataset:

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
            url=f"https://www.ebi.ac.uk/biostudies/BioImages/studies/{bia_study.accession_id}"
        )
    ]

    with open(output_fpath, "w") as fh:
        fh.write(ExportSODataset(**transform_dict).json(indent=2))

    return ExportSODataset(**transform_dict)

# FIXME - we get images twice...
def study_uuid_to_export_ai_dataset(study_uuid) -> ExportAIDataset:

    output_dirpath = settings.cache_root_dirpath / "datasets"
    output_dirpath.mkdir(exist_ok=True, parents=True)
    output_fpath = output_dirpath / f"{study_uuid}.json"
    if output_fpath.exists():
        return ExportDataset.parse_file(output_fpath)

    bia_study = rw_client.get_study(study_uuid, apply_annotations=True)

    images = get_images_with_a_rep_type(study_uuid, "ome_ngff")
    transform_dict = transform_ai_study_dict(bia_study)
    transform_dict["image_uuids"] = [image.uuid for image in images]
    transform_dict["links"] = [
        Link(
            name="original_submission",
            type="original_submission",
            url=f"https://www.ebi.ac.uk/biostudies/BioImages/studies/{bia_study.accession_id}"
        )
    ]
    transform_dict["annfile_uuids"] = get_annotation_file_uuids_by_study_uuid(study_uuid)
    
    
    annotation_files = get_annotation_files_by_study_uuid(study_uuid)
    
    ann_uuids_by_sourcename = get_ann_uuid_by_sourcename(annotation_files)
    #rich.print(ann_uuids_by_sourcename)

    transform_dict["corresponding_ann_uuids"] = {
        image.uuid: ann_uuids_by_sourcename.get(image.name)
        for image in images
    }

    im_uuid_by_name = {
        image.name: image.uuid for image in images
    }

    transform_dict["corresponding_im_uuids"] ={
        annfile.uuid : im_uuid_by_name.get(annfile.attributes['source image'])
        for annfile in annotation_files.values()
    }
    
    with open(output_fpath, "w") as fh:
        fh.write(ExportAIDataset(**transform_dict).json(indent=2))

    return ExportAIDataset(**transform_dict)


def study_uuid_to_export_images(study_uuid):
    study = rw_client.get_study(study_uuid)
    images = get_images_with_a_rep_type(study_uuid, "ome_ngff", limit=500)
    
    return {image.uuid: bia_image_to_export_image(image, study) for image in images}

def get_annotation_files_by_study_uuid(study_uuid):
    file_refs = get_file_references_by_study_uuid(study_uuid)
    return {fileref.uuid: fileref for fileref in file_refs
        if "source image" in fileref.attributes
    }

def get_ann_uuid_by_sourcename(annotation_files):
    ann_aliases_by_sourcename = {}
    for annfile in annotation_files.values():
        if ann_aliases_by_sourcename.get(annfile.attributes['source image']):
            ann_aliases_by_sourcename[annfile.attributes['source image']] += ', ' + annfile.uuid
        else:
            ann_aliases_by_sourcename[annfile.attributes['source image']] = annfile.uuid 
    return ann_aliases_by_sourcename

@app.command()
def show_export(accession_id: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)
    api_study = rw_client.get_study(study_uuid)

    export_dataset = study_uuid_to_export_dataset(study_uuid)

    # rich.print(api_study)
    rich.print(export_dataset)

@app.command()
def show_so_export(accession_id: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)
    study = rw_client.get_study(study_uuid, apply_annotations=True)
    sodict = transform_so_study_dict(study)

    export_dataset = study_uuid_to_export_sodataset(study_uuid)

    # rich.print(api_study)
    #rich.print(sodict)
    rich.print(export_dataset)

@app.command()
def show_fileref_export(accession_id: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)
    rich.print(get_annotation_files_by_study_uuid(study_uuid))


# @app.command()
# def 
# def show_image_export(accession_id: str, image_relpath: str):
    # image = get_image_by_accession_id_and_relpath(accession_id, image_relpath)
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
        "S-BSST223", "S-BSST429", "S-BIAD144", "S-BIAD217", "S-BIAD368", "S-BIAD425",
        "S-BIAD570","S-BIAD1009",
        "S-BIAD582", "S-BIAD606", "S-BIAD608", "S-BIAD620",
        "S-BIAD661", "S-BIAD626", "S-BIAD627", "S-BIAD725", "S-BIAD746", "S-BIAD826",
        "S-BIAD886", "S-BIAD901", "S-BIAD915", "S-BIAD916", "S-BIAD922", "S-BIAD928",
        "S-BIAD952", "S-BIAD954", "S-BIAD961", "S-BIAD963", "S-BIAD968", "S-BIAD976",
        "S-BIAD978", "S-BIAD987", "S-BIAD988", "S-BIAD993", "S-BIAD999", "S-BIAD1008",
        "S-BIAD1012", "S-BIAD1015", "S-BIAD1021", "S-BIAD1024",
        "S-BIAD531", "S-BIAD599", "S-BIAD463", "S-BIAD634", "S-BIAD686", "S-BIAD493"
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

    exports = Exports(
        images=export_images
    )

    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))


@app.command()
def export_defaults(output_filename: Path = Path("bia-export.json")):

    accession_ids = [
        "S-BSST223", "S-BSST429", "S-BIAD144", "S-BIAD217", "S-BIAD368", "S-BIAD425",
        "S-BIAD570",
        "S-BIAD582", "S-BIAD606", "S-BIAD608", "S-BIAD620",
        "S-BIAD661", "S-BIAD626", "S-BIAD627", "S-BIAD725", "S-BIAD746", "S-BIAD826",
        "S-BIAD886", "S-BIAD901", "S-BIAD915", "S-BIAD916", "S-BIAD922", "S-BIAD928",
        "S-BIAD952", "S-BIAD954", "S-BIAD961", "S-BIAD963", "S-BIAD968", "S-BIAD976",
        "S-BIAD978", "S-BIAD987", "S-BIAD988", "S-BIAD993", "S-BIAD999", "S-BIAD1008",
        "S-BIAD1012", "S-BIAD1015", "S-BIAD1021", "S-BIAD1024"
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

@app.command()
def ai_datasets(output_filename: Path = Path("bia-ai-export.json")):

    accession_ids = [
        "S-BIAD531", "S-BIAD599", "S-BIAD463", "S-BIAD634", "S-BIAD686", "S-BIAD493"]

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

    exports = AIExports(
        datasets=export_datasets,
        images=export_images
    )

    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))

@app.command()
def spatial_omics_datasets(output_filename: Path = Path("bia-spatialomics-export.json")):

    accession_ids = [
        "S-BIAD570", "S-BIAD1009"
    ]

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

    exports = SOExports(
        datasets=export_datasets,
        images=export_images
    )

    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))

@app.command()
def annotation_files(output_filename: Path = Path("bia-annotation_files.json")):

    accession_ids = [
        "S-BIAD531", "S-BIAD599", "S-BIAD463", "S-BIAD634", "S-BIAD686", "S-BIAD493"
    ]

    study_accession_ids_to_export = accession_ids

    study_uuids_by_accession_id = {
        accession_id: get_study_uuid_by_accession_id(accession_id)
        for accession_id in study_accession_ids_to_export
    }
    
    export_annotfiles = {}
    for study_uuid in study_uuids_by_accession_id.values():
        study_filerefs = get_file_references_by_study_uuid(study_uuid)
        export_filerefs = {fileref.uuid: fileref_to_export_annotations(fileref) for fileref in study_filerefs}
        export_annotfiles.update(export_filerefs)

    # FIXME - Write the proper export call
    exports = None
    with open(output_filename, "w") as fh:
        fh.write(exports.json(indent=2))


if __name__ == "__main__":
    app()
