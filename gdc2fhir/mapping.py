import os
import json
from pydantic import types
from gdc2fhir import utils
from gdc2fhir.schema import Schema, Map, Metadata, Version, Source, Destination, ContentAnnotation, Coding, Reference
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.patient import Patient
from fhir.resources.documentreference import DocumentReference


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
        reference=[source_ref]
    )

    destination = Destination(
        name=ResearchStudy.schema()['title'],
        description=utils.clean_description(ResearchStudy.schema()['description']),
        module='Administration',
        title=ResearchStudy.schema()['title'],
        type=ResearchStudy.schema()['type'],
        reference=[destination_ref]
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


def initialize_case(field_path="./resources/gdc_resources/fields/", out_path="./mapping/case_test.json"):
    """
    initial Schema structure of GDC Case

    :param field_path: Path to GDC fields json files
    :param out_path: Path to case json schema
    :return: saves initial json schema of GDC object for mapping
    """
    fields = utils.load_fields(field_path)

    metadata = Metadata(
        title="Case",
        category="case",
        type="object",
        downloadable=False,
        description="Mapping GDC case entities, properties, and relations to FHIR. GDC case is the collection of all data related to a specific subject in the context of a specific project.",
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

    references = [data_dict['case']['case']['links'][i]['target_type'] for i in
                  range(0, len(data_dict['case']['case']['links']))]
    source_refs = []
    for r in references:
        source_refs.append(Reference(
            reference_type=r
        ))

    source = Source(
        name=data_dict['case']['case']['id'],
        description=data_dict['case']['case']['description'],
        category=data_dict['case']['case']['category'],
        type=data_dict['case']['case']['type'],
        reference=source_refs
    )

    destination = Destination(
        name=Patient.schema()['title'],
        description=utils.clean_description(Patient.schema()['description']),
        module='Administration',
        title=Patient.schema()['title'],
        type=Patient.schema()['type']
    )

    obj_map = Map(
        source=source,
        destination=destination
    )

    case_schema = Schema(
        version="1",
        metadata=metadata,
        obj_mapping=obj_map,
        obj_keys=fields['case_fields'],
        source_key_required=[],
        destination_key_required=[],
        unique_keys=[],
        source_key_aliases=[],
        destination_key_aliases=[],
        mappings=[]
    )

    # validate schema
    Schema.check_schema(case_schema)

    schema_extra = case_schema.Config.schema_extra.get('$schema', None)
    case_schema_dict = case_schema.dict()
    case_schema_dict = {'$schema': schema_extra, **case_schema_dict}

    # write initial schema to json
    if os.path.exists(out_path):
        print(f"File: {out_path} exists.")
    else:
        with open(out_path, 'w') as j:
            json.dump(case_schema_dict, j, indent=4)


def initialize_file(field_path="./resources/gdc_resources/fields/", out_path="./mapping/file_test.json"):
    """
    initial Schema structure of GDC File

    :param field_path: Path to GDC fields json files
    :param out_path: Path to file json schema
    :return: saves initial json schema of GDC object for mapping
    """
    fields = utils.load_fields(field_path)

    metadata = Metadata(
        title="File",
        category="data_file",
        type="object",
        downloadable=True,
        description="Mapping GDC file to FHIR. GDC file is a set of related records (either written or electronic) kept together. (NCIt C42883)",
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

    # TODO: subgroup ref
    references = [i['target_type'] if 'subgroup' not in i
                  else [subgroup['target_type'] for subgroup in i['subgroup']]
                  for i in data_dict['file']['file']['links']]

    source_refs = []
    for r in references[0]:
        source_refs.append(Reference(
            reference_type=r
        ))

    source = Source(
        name=data_dict['file']['file']['id'],
        description=data_dict['file']['file']['description'],
        category=data_dict['file']['file']['category'],
        type=data_dict['file']['file']['type'],
        reference=source_refs
    )

    destination = Destination(
        name=DocumentReference.schema()['title'],
        description=utils.clean_description(DocumentReference.schema()['description']),
        module='Diagnostics',
        title=DocumentReference.schema()['title'],
        type=DocumentReference.schema()['type']
    )

    obj_map = Map(
        source=source,
        destination=destination
    )

    file_schema = Schema(
        version="1",
        metadata=metadata,
        obj_mapping=obj_map,
        obj_keys=fields['file_fields'],
        source_key_required=[],
        destination_key_required=[],
        unique_keys=[],
        source_key_aliases=[],
        destination_key_aliases=[],
        mappings=[]
    )

    # validate schema
    Schema.check_schema(file_schema)

    schema_extra = file_schema.Config.schema_extra.get('$schema', None)
    file_schema_dict = file_schema.dict()
    file_schema_dict = {'$schema': schema_extra, **file_schema_dict}

    # write initial schema to json
    if os.path.exists(out_path):
        print(f"File: {out_path} exists.")
    else:
        with open(out_path, 'w') as j:
            json.dump(file_schema_dict, j, indent=4)
