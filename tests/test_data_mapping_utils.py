from pytest_mock import mocker
from bia_export.data_mapping_utils import create_export_image


from .utils import (
    get_template_api_biosample,
    get_template_api_image_acquisition,
    get_template_api_specimen,
    get_template_api_study,
    get_template_api_image,
    get_template_export_image,
    add_image_representation,
    get_template_ome_zarr_image,
)


def test_create_export_image(mocker):
    # We patch ome_zarr_image_from_ome_zarr_uri in bia_export.data_mapping_utils even though it's defined in
    # bia_export.proxyimage. This is because we have to replace the method as it's being imported into bia_export.data_mapping_utils
    # so that when create_export_image is called it only has access the replacement.
    # Knowing where to patch is tricky, see: https://docs.python.org/3/library/unittest.mock.html#where-to-patch
    mocker.patch(
        "bia_export.data_mapping_utils.ome_zarr_image_from_ome_zarr_uri",
        return_value=get_template_ome_zarr_image(),
    )

    image = get_template_api_image()
    export_image = create_export_image(
        image=add_image_representation(image),
        study=get_template_api_study(),
        image_acquisitions=[get_template_api_image_acquisition()],
        specimens=[get_template_api_specimen()],
        biosamples=[get_template_api_biosample()],
    )
    template = get_template_export_image(image_uuid=image.uuid)

    assert template == export_image
