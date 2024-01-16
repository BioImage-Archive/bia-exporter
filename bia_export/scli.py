import logging

from pydantic import BaseSettings

from bia_integrator_api.util import simple_client
from bia_integrator_api import models as api_models, exceptions as api_exceptions

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    api_base_url: str = 'https://bia-cron-1.ebi.ac.uk:8080'
    bia_username: str = None
    bia_password: str = None
    disable_ssl_host_check: bool = True

    class Config:
        env_file = '.env'


settings = Settings()

rw_client = simple_client(
    api_base_url=settings.api_base_url,
    username=settings.bia_username,
    password=settings.bia_password,
    disable_ssl_host_check=settings.disable_ssl_host_check
)

def get_study_uuid_by_accession_id(accession_id: str):
    study_obj = rw_client.get_object_info_by_accession([accession_id])
    study_uuid = study_obj[0].uuid

    return study_uuid


def get_images_with_a_rep_type(study_uuid, rep_type, limit=5):

    images = rw_client.search_images_exact_match(
        api_models.SearchImageFilter(
            image_representations_any=[api_models.SearchFileRepresentation(
                type=rep_type,
            )],
            study_uuid=study_uuid,
            limit=limit
        ),
        apply_annotations=True
    )

    return images


def get_image_by_accession_id_and_relpath(accession_id: str, relpath: str):
    study_uuid = get_study_uuid_by_accession_id(accession_id)

    search_filter = api_models.SearchImageFilter(
        study_uuid=study_uuid,
        original_relpath=relpath
    )

    images = rw_client.search_images_exact_match(
        search_filter,
        apply_annotations=True
    )

    if len(images):
        return images[0]