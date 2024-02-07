import os
import json
from pydantic import types
from gdc2fhir import utils
from gdc2fhir.schema import Schema, Map, Metadata, Version, Source, Destination, ContentAnnotation, Coding, Reference
from fhir.resources.researchstudy import ResearchStudy

# Project -------------------------------------------
# read in project keys
# create header of schema and versions
# save json without Map mappings as initial structurae

data_dict = utils._data_dict


def initialize_project(field_path="./resources/gdc_resources/fields/", out_path="./mapping/project_test.json"):
    """
    initial Schema structure of GDC project

    :param field_path: Path to GDC fields json files
    :param out_path: Path to project json schema
    :return: saves initial json schema of GDC object to mapping
    """
    fields = utils.load_fields(field_path)

    metadata = Metadata(
        title="Project",
        category="project",
        type="object",
        downloadable=False,
        description="Mapping GDC project entities, properties, and relations to FHIR. GDC project is any specifically defined piece of work that is undertaken or attempted to meet a single requirement. (NCIt C47885)",
        versions=[
            Version(
                source_version="1",
                data_release="Data Release 39.0 - December 04, 2023",
                commit="023da73eee3c17608db1a9903c82852428327b88",
                status="OK",
                tag="5.0.6"

            ),
            Version(
                destination_version="5.0.0"
            )
        ],
        resource_links=["https://gdc.cancer.gov/about-gdc/gdc-overview", "https://www.hl7.org/fhir/overview.html"]
    )

    source_ref = Reference(
        reference_type=data_dict['administrative']['project']['links'][0]['target_type']
    )

    destination_ref = Reference(
        reference_type=ResearchStudy.schema()['properties']['partOf']['enum_reference_types'][0]
    )

    source = Source(
        name=data_dict['administrative']['project']['id'],
        description=data_dict['administrative']['project']['description'],
        category=data_dict['administrative']['project']['category'],
        type=data_dict['administrative']['project']['type'],
        reference=source_ref
    )

    destination = Destination(
        name=ResearchStudy.schema()['title'],
        description=utils.clean_description(ResearchStudy.schema()['description']),
        module='Administration',
        title=ResearchStudy.schema()['title'],
        type=ResearchStudy.schema()['type'],
        reference=destination_ref
    )

    obj_map = Map(
        source=source,
        destination=destination
    )

    project_schema = Schema(
        version="1",
        metadata=metadata,
        obj_mapping=obj_map,
        obj_keys=fields['project_fields'],
        source_key_required=[],
        destination_key_required=[],
        unique_keys=[],
        source_key_aliases=[],
        destination_key_aliases=[],
        mappings=[]
    )

    # validate schema
    Schema.check_schema(project_schema)

    schema_extra = project_schema.Config.schema_extra.get('$schema', None)
    project_schema_dict = project_schema.dict()
    project_schema_dict = {'$schema': schema_extra, **project_schema_dict}

    # write initial schema to json
    if os.path.exists(out_path):
        print(f"File: {out_path} exists.")
    else:
        with open(out_path, 'w') as j:
            json.dump(project_schema_dict, j, indent=4)
