from typing import Dict, List, Optional

from pydantic import BaseModel


class ExportCollection(BaseModel):
    name: str
    title: str
    subtitle: str
    description: str
    study_uuids: List[str]


class ExportImage(BaseModel):
    uuid: str
    name: str
    alias: str
    original_relpath: str
    study_title: str
    release_date: str

    vizarr_uri: str
    itk_uri: str | None

    study_accession_id: str
    thumbnail_uri: str

    sizeX: int
    sizeY: int
    sizeZ: int = 1
    sizeC: int = 1
    sizeT: int = 1

    source_image_uuid: str = None
    source_image_thumbnail_uri: str = None
    overlay_image_uri: str = None

    PhysicalSizeX: Optional[float] = None
    PhysicalSizeY: Optional[float] = None
    PhysicalSizeZ: Optional[float] = None

    attributes: Dict[str, str | None]


class Link(BaseModel):
    name: str
    type: str
    url: str

class ExportDataset(BaseModel):
    accession_id: str
    title: str
    release_date: str
    example_image_uri: str
    imaging_type: str
    organism: str
    n_images: int
    image_uuids: List[str]
    links: List[Link] = []


class Exports(BaseModel):
    collections: Dict[str, ExportCollection] = {}
    images: Dict[str, ExportImage]
    datasets: Dict[str, ExportDataset]

