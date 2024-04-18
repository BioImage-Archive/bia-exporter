import pytest
import json
import os
from bia_integrator_api import models as api_models
from bia_export.models import ExportImage


def test_base() -> str:
    return os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


@pytest.fixture(scope="module")
def bia_image() -> api_models.BIAImage:
    with open(os.path.join(test_base(), "data/input", "bia_image.json")) as f:
        return api_models.BIAImage(**json.load(f))


@pytest.fixture(scope="module")
def bia_study() -> api_models.BIAStudy:
    with open(os.path.join(test_base(), "data/input", "bia_study.json")) as f:
        return api_models.BIAStudy(**json.load(f))


@pytest.fixture(scope="module")
def website_image() -> ExportImage:
    with open(os.path.join(test_base(), "data/output", "website_image.json")) as f:
        return ExportImage(**json.load(f))
