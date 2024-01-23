import json
import requests
from fhir.resources.patient import Patient
from fhir.resources.documentreference import DocumentReference
from fhir.resources.coding import Coding
from fhir.resources.observation import Observation
from fhir.resources.extension import Extension
from fhir.resources.researchstudy import ResearchStudy
# TODO: OOP vs. utility

Coding.schema()['properties']['code']['description']
Patient.schema()['properties']
DocumentReference.schema()['properties']
Observation.schema()['properties']
Extension.schema()['properties']
ResearchStudy.schema()['properties']


def extract_keys(data, parent_key=None, keys=None):
    """
    Extracts all keys in a nested dictionary and applies dot notation to capture nested keys hierarchy

    :param data: Dictionary or containing nested dictionaries
    :param parent_key: Parent key to build the hierarchy
    :param keys: List to store the extracted keys
    :return: List of all keys present
    """
    if keys is None:
        keys = []

    if isinstance(data, dict):
        for key, value in data.items():
            current_key = key if parent_key is None else f"{parent_key}.{key}"
            keys.append(current_key)
            extract_keys(value, parent_key=current_key, keys=keys)

    return keys


def get_key_hierarchy(json_path):
    """
    Reads a json file via a GDC scraper script json output ex.
    https://github.com/bmeg/bmeg-etl/blob/develop/transform/gdc/gdc-scan.py
    parses each line, and calls extract_keys() to capture keys hierarchy fetched from GDC

    :param json_path: Path to the JSON file
    :return: List of *all keys present in JSON file
    """
    extracted_keys_list = []

    with open(json_path, 'r') as file:
        for line in file:
            try:
                json_data = json.loads(line)
                extracted_keys = extract_keys(json_data)
                extracted_keys_list.extend(extracted_keys)
            except json.JSONDecodeError as e:
                print("Error decoding JSON: {}".format(e))

    return extracted_keys_list


JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "version": "",
    "metadata": {
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
    },
    "obj_mapping": {
        "source": {
            "name": "",
            "url": "",
            "description": "",
            "description_url": "",
            "category": "",
            "type": ""
        },
        "destination": {
            "name": "",
            "title": "",
            "url": "",
            "description": "",
            "description_url": "",
            "module": "",
            "type": ""
        }
    },
    "obj_keys": [],
    "source_key_required": [],
    "destination_key_required": [],
    "unique_keys": [],
    "source_key_aliases": {},
    "destination_key_aliases": {},
    "mappings": []
}

MAPPING_TEMPLATE = {
    "source": {
        "name": "",
        "url": "",
        "description": "",
        "description_url": "",
        "category": "",
        "type": ""
    },
    "destination": {
        "name": "",
        "url": "",
        "description": "",
        "description_url": "",
        "module": "",
        "type": ""
    }
}


def create_mapping(mapping_template, key):
    """
    Creates a mapping for a given key based on the template.

    :param mapping_template: Template for the mapping structure
    :param key: Key to be included in the mapping
    :return: Mapping for the key
    """
    mapping = json.loads(mapping_template)
    mapping["source"]["name"] = key
    return mapping


def initialize_json_schema(keys, out_path, mapping_template=json.dumps(MAPPING_TEMPLATE),
                           json_schema=json.dumps(JSON_SCHEMA), source_version="",
                           destination_version="", json_schema_version="1.0.0"):
    """
    Generates an empty schema json file with all source keys of interest to be mapped to destination keys.

    :param keys: List of keys to be included in the schema
    :param out_path: Output file path for the generated schema
    :param mapping_template: Template for the mapping structure
    :param json_schema: JSON schema template
    :param source_version: Source version for the schema
    :param destination_version: Destination version for the schema
    :param json_schema_version: Version of the JSON schema
    :return: Initial empty schema json file with all source keys to be mapped
    """
    mappings = [create_mapping(mapping_template, key) for key in keys]

    if json_schema is None:
        json_schema = {"version": json_schema_version, "metadata": {"versions": [{"source_version": source_version,
                                                                                  "destination_version": destination_version}]}}
    else:
        try:
            json_schema = json.loads(json_schema)
        except json.JSONDecodeError as e:
            print("Error decoding JSON schema: {}".format(e))
            return None

    json_schema["mappings"] = mappings

    with open(out_path, 'w') as json_file:
        json.dump(json_schema, json_file, indent=4)

    return json_schema


# TODO: other methods vs API get call data fetch
def gdc_data_dict(entity_name):
    """
    Fetches data dictionary for a specified entity from GDC API.
    TODO: pass version - or get data dict from python client

    :param entity_name: Name of GDC entity ex. project, case, file, annotation
    :return: Json schema data dictionary for the entity - none if error occurs
    """
    api_url = f"https://api.gdc.cancer.gov/v0/submission/_dictionary/{entity_name}"
    response = requests.get(api_url)

    if response.status_code == 200:
        entity_data = response.json()
        return entity_data
    else:
        print(f"Error: Unable to fetch data for entity {entity_name}. Status code: {response.status_code}")
        return None


# TODO: remove use-cases
demographic_dict = gdc_data_dict("demographic")
project_dict = gdc_data_dict("project")
case_dict = gdc_data_dict("case")
primary_sites = case_dict['properties']['primary_site']['enum']
disease_types = case_dict['properties']['disease_type']['enum']


def initialize_content_annotations(annot_enum, out_path):
    """
    Generates the initial list dictionary of content annotations to annotate

    :param annot_enum: List of annotations strings
    :param out_path: File path for the generated JSON.
    :return: List of dictionaries with each content annotation name as value's key
    """
    obj_list = []

    for item in annot_enum:
        content_annotation = {
            "value": item,
            "description": "",
            "description_url": "",
            "annotation_type": "",
            "annotation_url": ""
            # "ontology_url": "",
            # "sctid": ""
        }
        obj_list.append(content_annotation)

    jr = json.dumps(obj_list, indent=4)

    if out_path:
        with open(out_path, "w") as output_file:
            output_file.write(jr)


def gdc_api_version_data_info(api_version="v0"):
    api_url = f"https://api.gdc.cancer.gov/{api_version}/status"
    response = requests.get(api_url)

    if response.status_code == 200:
        return response.json()


def generate_content_annotations(data, out_path):
    """

    :param data: GDC data dictionary containing enum values and definitions.
    :param out_path: File path for annotations.
    """
    annotations = []

    for enum_value in data['enum']:
        if enum_value in data['enumDef']:
            enum_data = data['enumDef'][enum_value]
            definition = enum_data.get('description', 'No description available')
            term_url = enum_data['termDef'].get('term_url', '')

            annotations.append({
                "value": enum_value,
                "description": definition,
                "description_url": term_url,
                "annotation_type": enum_data['termDef'].get('source', ''),
                "annotation_url": term_url
            })
        else:
            annotations.append({
                "value": enum_value,
                "description": '',
                "description_url": '',
                "annotation_type": '',
                "annotation_url": ''
            })

    with open(out_path, 'w', encoding='utf-8') as file:
        json.dump(annotations, file, indent=4)


# TODO: remove use-cases
generate_content_annotations(demographic_dict['properties']['race'], "content_annotations/demographic/race.json")
generate_content_annotations(demographic_dict['properties']['ethnicity'], "content_annotations/demographic/ethnicity.json")
generate_content_annotations(case_dict['properties']['disease_type'], "content_annotations/case/disease_type.json")
generate_content_annotations(case_dict['properties']['primary_site'], "content_annotations/case/primary_site.json")


# 1 - fetch schema from FHIR
# ex. Coding.schema()['properties']['code']['description']
# 2- add function to extract element_required for all destination keys required
# 3 - pull out FHIR hierarchy from enum_reference_types ex.
"""
{'title': 'Part of larger study',
 'description': 'A larger research study of which this particular study is a component or step.',
 'element_property': True,
 'enum_reference_types': ['ResearchStudy'],
 'type': 'array',
 'items': {'type': 'Reference'}}
"""
# 4 - map node relation based on uppercase classes ex. extention for patient etc.

