from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class Source(BaseModel):
    # map types via this standard: https://docs.pydantic.dev/latest/concepts/types/
    name: str = Field(...)
    description: str = Field(...)
    description_url: str | None = Field(None)
    category: str | None = Field(None)
    type: str = Field(...)
    format: str | None = Field(None)
    enums: List[dict] | None = None
    content_annotation: list | str | None = None


class Destination(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    description_url: str | None = Field(None)
    module: str = Field(...)
    title: str = Field(...)
    type: str = Field(...)
    format: str | None = Field(None)


class Map(BaseModel):
    source: Source
    destination: Destination


class Schema(BaseModel):
    metadata: dict = Field(..., description='Metadata on GDC object and FHIR resources.')
    obj_mapping: Map = Field(..., description="The GDC object being mapped.")
    obj_key: List[str] = Field(..., description='GDC available field names')
    mappings: List[Map]


meta = {
    "title": "",
    "category": "",
    "type": "",
    "downloadable": False,
    "description": "",
    "versions": [
        {
            "source_version": ""
        },
        {
            "destination_version": ""
        }
    ],
    "resource_links": []
}


mappings = [
        {
            "source": {
                "name": "case",
                "description": "The collection of all data related to a specific subject in the context of a specific project.",
                "type": "object"
            }
        },
        {
            "destination": {
                "name": "Patient",
                "title": "Patient",
                "description": "Information about an individual or animal receiving health care services. Demographics and other administrative information about an individual or animal receiving care or ot her health-related services.",
                "description_url": "",
                "module": "Administration",
                "type": "object"
            }
        }
]

M1 = Map(**{"source": {
                "name": "case",
                "description": "The collection of all data related to a specific subject in the context of a specific project.",
                "type": "object"
            },
    "destination": {
                "name": "Patient",
                "title": "Patient",
                "description": "Information about an individual or animal receiving health care services. Demographics and other administrative information about an individual or animal receiving care or ot her health-related services.",
                "module": "Administration",
                "type": "object"
            }})

M2 = Map(**{"source": {
                "name": "case",
                "description": "The collection of all data related to a specific subject in the context of a specific project.",
                "type": "object"
            },
    "destination": {
                "name": "Patient",
                "title": "Patient",
                "description": "Information about an individual or animal receiving health care services. Demographics and other administrative information about an individual or animal receiving care or ot her health-related services.",
                "module": "Administration",
                "type": "object"
            }})

test_schema = Schema(**{"metadata": meta, "obj_mapping": M1, "obj_key": ["submitter_id", "case_id"], "mappings": [M1, M2]})
test_schema.json()

