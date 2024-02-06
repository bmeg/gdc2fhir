from __future__ import annotations
from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field, validate_model


class Source(BaseModel):
    # map types via this standard: https://docs.pydantic.dev/latest/concepts/types/
    name: str = Field(...)
    description: str = Field(...)
    description_url: Optional[str] = Field(None)
    category: Optional[str] = Field(None)
    type: str = Field(...)
    format: Optional[str] = Field(None)
    enums: Optional[List[dict]] = None
    content_annotation: Optional[Union[List[dict], str]] = None


class Destination(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    description_url: Optional[str] = Field(None)
    module: str = Field(...)
    title: str = Field(...)
    type: str = Field(...)
    format: Optional[str] = Field(None)


class Map(BaseModel):
    source: Source
    destination: Destination

    # store maps internally with source name as key to access faster
    _map_dict: Dict[str, Map] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._map_dict[self.source.name] = self

    @staticmethod
    def update_fields(model: BaseModel, values: Dict):
        for field, value in values.items():
            setattr(model, field, value)

    @staticmethod
    def update_values(source_name: str, source_values: Optional[Dict] = None, destination_values: Optional[Dict] = None):
        map_instance = Map._map_dict.get(source_name)
        if map_instance:
            if source_values:
                Map.update_fields(map_instance.source, source_values)
            if destination_values:
                Map.update_fields(map_instance.destination, destination_values)

    @classmethod
    def find_source(cls, source_name: str) -> Optional[Source]:
        map_instance = cls._map_dict.get(source_name)
        if map_instance:
            return map_instance.source

    @classmethod
    def find_destination(cls, destination_name: str) -> Optional[Destination]:
        map_instance = cls._map_dict.get(destination_name)
        if map_instance:
            return map_instance.destination

    @classmethod
    def check_map(cls, map_instance: Map) -> Map:
        *_, validation_error = validate_model(map_instance.__class__, map_instance.__dict__)
        if validation_error:
            raise validation_error


class Schema(BaseModel):
    metadata: dict = Field(default_factory=dict, description='Metadata on GDC object and FHIR resources.')
    obj_mapping: Map = Field(..., description="The GDC object being mapped.")
    obj_key: List[str] = Field(..., description='GDC available field names')
    mappings: List[Map]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def source_map_dict(self):
        return {mapping.source.name: mapping for mapping in self.mappings}

    @property
    def destination_map_dict(self):
        return {mapping.destination.name: mapping for mapping in self.mappings}

    def find_map_by_source(self, source_name: str) -> Optional[Map]:
        return self.source_map_dict.get(source_name)

    def find_map_by_destination(self, destination_name: str) -> Optional[Map]:
        return self.destination_map_dict.get(destination_name)

    def has_map_for_source(self, source_key: str) -> bool:
        return any(mapping.source.name == source_key for mapping in self.mappings)

    def has_map_for_destination(self, destination_key: str) -> bool:
        return any(mapping.destination.name == destination_key for mapping in self.mappings)

    def check_schema(self) -> Schema:
        *_, validation_error = validate_model(self.__class__, self.__dict__)
        if validation_error:
            raise validation_error


