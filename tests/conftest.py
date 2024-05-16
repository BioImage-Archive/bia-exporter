import pytest
from bia_integrator_api import models as api_models
from bia_export.models import ExportImage
from .utils import (
    get_template_api_biosample,
    get_template_api_image_acquisition,
    get_template_api_specimen,
    get_template_api_study,
    get_template_api_image,
    get_template_export_image,
    add_image_representation,
)


@pytest.fixture()
def bia_image() -> api_models.BIAImage:
    return get_template_api_image()


@pytest.fixture()
def bia_image_with_image_rep(bia_image) -> api_models.BIAImage:
    return add_image_representation(bia_image)


@pytest.fixture()
def bia_study() -> api_models.BIAStudy:
    return get_template_api_study()


@pytest.fixture()
def bia_image_acquisition() -> api_models.ImageAcquisition:
    return get_template_api_image_acquisition()


@pytest.fixture()
def bia_specimen() -> api_models.Specimen:
    return get_template_api_specimen()


@pytest.fixture()
def bia_biosample() -> api_models.Biosample:
    return get_template_api_biosample()


@pytest.fixture()
def website_image() -> ExportImage:
    return get_template_export_image()
