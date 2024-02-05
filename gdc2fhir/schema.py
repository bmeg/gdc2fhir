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

    