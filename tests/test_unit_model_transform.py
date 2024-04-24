from bia_export.cli import bia_image_to_export_image
from bia_export.models import ExportImage

from bia_integrator_api import models as api_models


def test_bia_image_to_export_image(
    bia_image: api_models.BIAImage,
    bia_study: api_models.BIAStudy,
    website_image: ExportImage,
):
    # Test currently relies on the example data not having any of:
    # BioSample, Specimen and ImageAcquisition
    # in order to not call the api.
    # TODO: use mocking to avoid api calls
    export_image = bia_image_to_export_image(
        image=bia_image, study=bia_study, use_cache=False
    )

    assert website_image == export_image
