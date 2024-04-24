# Helper functions for converting between data representations.
# These tend to accept instances of classes defined in bia_integrator_api.models
# and return transformed data or instances of classes defined in bia_export.models.

from pathlib import Path
from bia_integrator_api import models as api_models
from .models import ExportImage
from .proxyimage import ome_zarr_image_from_ome_zarr_uri


def filter_image_attributes(image: api_models.BIAImage) -> dict[str, str]:
    """Given a BIA Image, filter the attributes for those we wish to export
    and return as dict."""

    def filter_func(key):
        if key == "channels":
            return False
        if "channel" in key.lower():
            return True

        return False

    return {key: value for key, value in image.attributes.items() if filter_func(key)}


def transform_study_dict(bia_study: api_models.BIAStudy) -> dict:
    keys = [
        "accession_id",
        "title",
        "release_date",
        "example_image_uri",
        "imaging_type",
        "organism",
    ]
    base_dict = {key: bia_study.__dict__[key] for key in keys}

    base_dict["n_images"] = bia_study.images_count

    return base_dict


def transform_ai_study_dict(bia_study: api_models.BIAStudy) -> dict:
    keys = [
        "accession_id",
        "title",
        "release_date",
        "example_image_uri",
        "imaging_type",
        "organism",
    ]
    base_dict = {key: bia_study.__dict__[key] for key in keys}

    keys2 = [
        "example_annotation_uri",
        "annotation_type",
        "annotation_method",
        "models_description",
        "models_uri",
    ]
    base_dict.update({key: bia_study.attributes.get(key) for key in keys2})

    base_dict["n_images"] = bia_study.images_count

    return base_dict


def transform_so_study_dict(bia_study: api_models.BIAStudy):
    keys = [
        "accession_id",
        "title",
        "release_date",
        "example_image_uri",
        "imaging_type",
        "organism",
    ]
    base_dict = {key: bia_study.__dict__[key] for key in keys}

    keys2 = [
        # 'example_annotation_uri',
        # 'annotation_type',
        # 'annotation_method',
        # 'models_description',
        # 'models_uri',
        "scseq_desc",
        "scseq_link",
        "code_desc",
        "code_link",
    ]
    base_dict.update({key: bia_study.attributes.get(key) for key in keys2})

    base_dict["n_images"] = bia_study.images_count

    return base_dict


def create_export_image(
    image: api_models.BIAImage,
    study: api_models.BIAStudy,
    image_acquisitions: list[api_models.ImageAcquisition],
    specimens: list[api_models.Specimen],
    biosamples: list[api_models.Biosample],
) -> ExportImage:
    reps_by_type = {rep.type: rep for rep in image.representations}

    ome_zarr_uri = reps_by_type["ome_ngff"].uri[0]
    im = ome_zarr_image_from_ome_zarr_uri(ome_zarr_uri)

    try:
        thumbnail_uri = reps_by_type["thumbnail"].uri[0]
    except KeyError:
        thumbnail_uri = ""

    source_image_uuid = image.attributes.get("source_image_uuid", None)
    source_image_thumbnail_uri = image.attributes.get(
        "source_image_thumbnail_uri", None
    )
    overlay_image_uri = image.attributes.get("overlay_image_uri", None)

    itk_base = "https://kitware.github.io/itk-vtk-viewer/app/?fileToLoad="
    vizarr_base = (
        "https://uk1s3.embassy.ebi.ac.uk/bia-zarr-test/vizarr/index.html?source="
    )

    export_im = ExportImage(
        uuid=image.uuid,
        name=Path(image.name).name,
        alias="IM1",
        original_relpath=image.original_relpath,
        thumbnail_uri=thumbnail_uri,
        study_accession_id=study.accession_id,
        study_title=study.title,
        release_date=study.release_date,
        itk_uri=itk_base + reps_by_type["ome_ngff"].uri[0],
        vizarr_uri=vizarr_base + reps_by_type["ome_ngff"].uri[0],
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
        attributes=filter_image_attributes(image),
    )

    if len(image_acquisitions) > 0:
        export_im.image_acquisition_title = image_acquisitions[0].title
        export_im.image_acquisition_imaging_instrument = image_acquisitions[
            0
        ].imaging_instrument
        export_im.image_acquisition_image_acquisition_parameters = image_acquisitions[
            0
        ].image_acquisition_parameters
        export_im.image_acquisition_imaging_method = image_acquisitions[
            0
        ].imaging_method

    if len(specimens) > 0:
        export_im.specimen_title = specimens[0].title
        export_im.specimen_sample_preparation_protocol = specimens[
            0
        ].sample_preparation_protocol
        export_im.specimen_growth_protocol = specimens[0].growth_protocol

    if len(biosamples) > 0:
        export_im.biosample_title = biosamples[0].title
        export_im.biosample_organism_scientific_name = biosamples[
            0
        ].organism_scientific_name
        export_im.biosample_organism_common_name = biosamples[0].organism_common_name
        export_im.biosample_organism_ncbi_taxon = biosamples[0].organism_ncbi_taxon
        export_im.biosample_description = biosamples[0].description
        export_im.biosample_biological_entity = biosamples[0].biological_entity
        export_im.biosample_experimental_variables = ", ".join(
            biosamples[0].experimental_variables
        )
        export_im.biosample_extrinsic_variables = ", ".join(
            biosamples[0].extrinsic_variables
        )
        export_im.biosample_intrinsic_variables = ", ".join(
            biosamples[0].intrinsic_variables
        )

    return export_im


def get_ann_uuid_by_sourcename(annotation_files: dict):
    ann_aliases_by_sourcename = {}
    for annfile in annotation_files.values():
        if ann_aliases_by_sourcename.get(annfile.attributes["source image"]):
            ann_aliases_by_sourcename[annfile.attributes["source image"]] += (
                ", " + annfile.uuid
            )
        else:
            ann_aliases_by_sourcename[annfile.attributes["source image"]] = annfile.uuid
    return ann_aliases_by_sourcename
