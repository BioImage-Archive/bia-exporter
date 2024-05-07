from bia_integrator_api import models as api_models
from bia_export.models import ExportImage
from bia_export.proxyimage import OMEZarrImage
import uuid


def get_template_api_study(study_uuid=uuid.uuid4(), accession_id="S-BIAXXXX"):
    placeholder_fields = {
        "uuid": str(study_uuid),
        "version": 0,
        "model": {"type_name": "BIAStudy", "version": 1},
        "accession_id": accession_id,
        "title": "placeholder_study_title",
        "description": "description",
        "attributes": {},
        "example_image_annotation_uri": "",
        "example_image_uri": "",
        "imaging_type": None,
        "authors": [],
        "tags": [],
        "organism": "test",
        "release_date": "test",
        "file_references_count": 0,
        "images_count": 0,
        "annotations_applied": False,
        "annotations": [],
        "@context": "https://placeholder.uri/",
    }
    return api_models.BIAStudy(**placeholder_fields)


def get_template_api_biosample(biosample_uuid=uuid.uuid4()):
    placeholder_fields = {
        "uuid": str(biosample_uuid),
        "version": 0,
        "title": "placeholder_title",
        "organism_scientific_name": "placeholder_organism_scientific_name",
        "organism_common_name": "placeholder_organism_common_name",
        "organism_ncbi_taxon": "placeholder_organism_ncbi_taxon",
        "description": "placeholder_description",
        "biological_entity": "placeholder_biological_entity",
        "experimental_variables": ["placeholder_experimental_variable"],
        "extrinsic_variables": ["placeholder_extrinsic_variable"],
        "intrinsic_variables": ["placeholder_intrinsic_variable"],
        "annotations_applied": False,
        "attributes": {},
        "annotations": [],
        "@context": "https://placeholder.uri/",
    }
    return api_models.Biosample(**placeholder_fields)


def get_template_api_specimen(specimen_uuid=uuid.uuid4(), biosample_uuid=uuid.uuid4()):
    placeholder_fields = {
        "uuid": str(specimen_uuid),
        "version": 0,
        "biosample_uuid": str(biosample_uuid),
        "title": "placeholder_specimen_title",
        "sample_preparation_protocol": "placeholder_sample_preparation_protocol",
        "growth_protocol": "placeholder_growth_protocol",
        "annotations_applied": False,
        "attributes": {},
        "annotations": [],
        "@context": "https://placeholder.uri/",
    }
    return api_models.Specimen(**placeholder_fields)


def get_template_api_image_acquisition(
    acquisition_uuid=uuid.uuid4(), specimen_uuid=uuid.uuid4()
):
    placeholder_fields = {
        "uuid": str(acquisition_uuid),
        "version": 0,
        "specimen_uuid": str(specimen_uuid),
        "title": "placeholder_title",
        "imaging_instrument": "placeholder_imaging_instrument",
        "image_acquisition_parameters": "placeholder_image_acquisition_parameters",
        "imaging_method": "placeholder_imaging_method",
        "annotations_applied": False,
        "attributes": {},
        "annotations": [],
        "@context": "https://placeholder.uri/",
    }
    return api_models.ImageAcquisition(**placeholder_fields)


def get_template_api_image(image_uuid=uuid.uuid4(), study_uuid=uuid.uuid4()):
    placeholder_fields = {
        "uuid": str(image_uuid),
        "version": 0,
        "study_uuid": str(study_uuid),
        "model": {"type_name": "BIAImage", "version": 2},
        "name": "image_name_value",
        "original_relpath": "/home/test/image_path_value",
        "attributes": {
            "k": "v",
        },
        "annotations": [],
        "annotations_applied": False,
        "dimensions": None,
        "alias": None,
        "representations": [],
        "image_acquisitions_uuid": [],
        "@context": "https://placeholder.uri/",
    }
    return api_models.BIAImage(**placeholder_fields)


def add_image_representation(image: api_models.BIAImage):
    ome_ngff_rep = {
        "size": 0,
        "uri": ["https://placeder.uri/file.zarr/0"],
        "type": "ome_ngff",
        "dimensions": None,
        "attributes": {},
        "rendering": None,
    }
    image.representations.append(api_models.BIAImageRepresentation(**ome_ngff_rep))
    return image


def get_template_ome_zarr_image():
    placeholder_fields = {
        "sizeX": 1,
        "sizeY": 1,
        "sizeZ": 1,
        "sizeC": 1,
        "sizeT": 1,
        "n_scales": 1,
        "xy_scaling": 1.0,
        "z_scaling": 1.0,
        "path_keys": [],
        "PhysicalSizeX": None,
        "PhysicalSizeY": None,
        "PhysicalSizeZ": None,
        "ngff_metadata": None,
    }
    return OMEZarrImage(**placeholder_fields)


def get_template_export_image(image_uuid=uuid.uuid4(), study_accession_id="S-BIAXXXX"):
    placeholder_fields = {
        "uuid": str(image_uuid),
        "name": "image_name_value",
        "alias": "IM1",
        "original_relpath": "/home/test/image_path_value",
        "study_title": "placeholder_study_title",
        "release_date": "test",
        "vizarr_uri": "https://uk1s3.embassy.ebi.ac.uk/bia-zarr-test/vizarr/index.html?source=https://placeder.uri/file.zarr/0",
        "itk_uri": "https://kitware.github.io/itk-vtk-viewer/app/?fileToLoad=https://placeder.uri/file.zarr/0",
        "study_accession_id": str(study_accession_id),
        "thumbnail_uri": "",
        "sizeX": 1,
        "sizeY": 1,
        "sizeZ": 1,
        "sizeC": 1,
        "sizeT": 1,
        "source_image_uuid": None,
        "source_image_thumbnail_uri": None,
        "overlay_image_uri": None,
        "PhysicalSizeX": None,
        "PhysicalSizeY": None,
        "PhysicalSizeZ": None,
        "biosample_title": "placeholder_title",
        "biosample_organism_scientific_name": "placeholder_organism_scientific_name",
        "biosample_organism_common_name": "placeholder_organism_common_name",
        "biosample_organism_ncbi_taxon": "placeholder_organism_ncbi_taxon",
        "biosample_description": "placeholder_description",
        "biosample_biological_entity": "placeholder_biological_entity",
        "biosample_experimental_variables": "placeholder_experimental_variable",
        "biosample_extrinsic_variables": "placeholder_extrinsic_variable",
        "biosample_intrinsic_variables": "placeholder_intrinsic_variable",
        "specimen_title": "placeholder_specimen_title",
        "specimen_sample_preparation_protocol": "placeholder_sample_preparation_protocol",
        "specimen_growth_protocol": "placeholder_growth_protocol",
        "image_acquisition_title": "placeholder_title",
        "image_acquisition_imaging_instrument": "placeholder_imaging_instrument",
        "image_acquisition_image_acquisition_parameters": "placeholder_image_acquisition_parameters",
        "image_acquisition_imaging_method": "placeholder_imaging_method",
        "attributes": {},
    }
    return ExportImage(**placeholder_fields)
