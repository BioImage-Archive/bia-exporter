from bia_export.cli import bia_image_to_export_image
from bia_export.models import ExportImage
from bia_export.scli import rw_client

from bia_integrator_api import models as api_models
import unittest
from unittest.mock import patch, Mock


def test_bia_image_to_export_image(
    bia_image: api_models.BIAImage,
    bia_study: api_models.BIAStudy,
    website_image: ExportImage,
    mocker,
):
    # mocker.patch("rw_client.get_image_acquisition").return_value.specimen_uuid = (
    #     "Valid UUID"
    # )
    # mocker.patch("..scli.rw_client.get_specimen").return_value.biosample_uuid = (
    #     "Valid UUID"
    # )
    # mocker.patch("..scli.rw_client.get_image_acquisition").return_value = "Valid UUID"

    export_image = bia_image_to_export_image(
        image=bia_image, study=bia_study, use_cache=False
    )

    assert website_image == export_image
