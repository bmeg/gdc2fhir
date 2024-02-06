import pytest
from gdc2fhir.schema import Schema, Source, Destination, Map


@pytest.fixture
def example_schema():
    # schema for testing
    source_obj = Source(
        name="case",
        description="The collection of all data related to a specific subject in the context of a specific project.",
        type="object"
    )

    destination_obj = Destination(
        name="Patient",
        description="This is a patient",
        module="Administration",
        title="Patient",
        type="object"
    )

    map_obj = Map(source=source_obj, destination=destination_obj)

    source_a = Source(
        name="case_id",
        description="UUID",
        type="object"
    )

    destination_a = Destination(
        name="Patient.identifier",
        description="some description",
        module="Administration",
        title="Patient.identifier",
        type="object"
    )

    map1 = Map(source=source_a, destination=destination_a)

    source_b = Source(
        name="sample_id",
        description="A 128-bit identifier.",
        type="object"
    )

    destination_b = Destination(
        name="Specimen.identifier",
        description="Id for specimen.",
        module="AnotherModule",
        title="AnotherTitle",
        type="object"
    )

    map2 = Map(source=source_b, destination=destination_b)

    return Schema(
        metadata={"title": "Case", "downloadable": False},
        obj_mapping=map_obj,
        obj_key=["case_id", "sample_id"],
        mappings=[map1, map2]
    )


def test_find_source(example_schema):
    found_source = example_schema.find_map_by_source(source_name="case_id").source
    assert found_source is not None
    assert found_source.name == "case_id"


def test_has_map_for_source(example_schema):
    assert example_schema.has_map_for_source("case_id")
    assert not example_schema.has_map_for_source("NonExistentDestination")


def test_find_destination(example_schema):
    found_map = example_schema.find_map_by_destination(destination_name="Patient.identifier")
    assert found_map is not None
    assert found_map.destination.name == "Patient.identifier"


def test_has_map_for_destination(example_schema):
    assert example_schema.has_map_for_destination("Patient.identifier")
    assert not example_schema.has_map_for_destination("NonExistentDestination")


def test_find_and_update_values(example_schema):
    source_name = "case_id"
    source_values = {"description": "Unique key of entity"}

    # Find map by source name
    map_instance = example_schema.find_map_by_source(source_name=source_name)
    assert map_instance is not None

    # Update its values
    Map.update_values(source_name=source_name, source_values=source_values)

    # Check updates
    updated_source = example_schema.find_map_by_source(source_name=source_name).source
    assert updated_source is not None
    assert updated_source.description == "Unique key of entity"

