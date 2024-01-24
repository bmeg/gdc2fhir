import json
import requests
from bs4 import BeautifulSoup
from fhir.resources.patient import Patient
from fhir.resources.documentreference import DocumentReference
from fhir.resources.coding import Coding
from fhir.resources.observation import Observation
from fhir.resources.observationdefinition import ObservationDefinition
from fhir.resources.extension import Extension
from fhir.resources.researchstudy import ResearchStudy, ResearchStudyRecruitment, ResearchStudyProgressStatus
from fhir.resources.genomics import GenomicStudyAnalysis
from fhir.resources.researchsubject import ResearchSubject
from fhir.resources.specimen import Specimen

# TODO: OOP vs. utility

Coding.schema()['properties']['code']['description']
Patient.schema()['properties']
DocumentReference.schema()['properties']
Observation.schema()['properties']
Extension.schema()['properties']
ResearchStudy.schema()['properties']
GenomicStudyAnalysis.schema()['properties']['changeType']
ResearchSubject.schema()['properties']
Specimen.schema()['properties']['identifier']


def get_field_text(table):
    """
    Gets text of td tags of an xml table

    :param table: xml data in an html table
    :return: list of GDC fields
    """
    fields = []
    rows = table.find_all("td", recursive=True)
    for td in rows:
        fields.append(td.get_text())
    return fields


def gdc_available_fields():
    """
    Fetch available fields via GDC site

    :return: Dictionary of project, case, and file fields
    """
    response = requests.get("https://docs.gdc.cancer.gov/API/Users_Guide/Appendix_A_Available_Fields/")

    if response.status_code == 200:
        html_content = response.content.decode("utf-8")

        soup = BeautifulSoup(html_content, 'lxml')
        field_tables = soup.find_all("table", recursive=True)
        project_fields = get_field_text(field_tables[0])
        case_fields = get_field_text(field_tables[1])
        file_fields = get_field_text(field_tables[2])
        return {"project_fields": project_fields, "case_fields": case_fields, "file_fields": file_fields}
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


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
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, dict):
                current_key = f"{parent_key}" if parent_key is not None else str(index)
                keys.append(current_key)
                extract_keys(item, parent_key=current_key, keys=keys)
            else:
                current_key = f"{parent_key}" if parent_key is not None else ""
                keys.append(current_key)

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
            "description": "",
            "description_url": "",
            "category": "",
            "type": ""
        },
        "destination": {
            "name": "",
            "title": "",
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
        "description": "",
        "description_url": "",
        "category": "",
        "type": ""
    },
    "destination": {
        "name": "",
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
    json_meta = {"version": json_schema_version, "metadata": {
        "versions": [{"source_version": source_version, "destination_version": destination_version}]}, "obj_keys": keys}

    json_schema = json.loads(json_schema)
    json_schema.update(json_meta)

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


def update_values(schema, name, mapping_key="source", new_values=None):
    """
    Updates values of source or destination keys

    :param schema: Json schema to be updated
    :param name: name of source or destination dictionary to be updated
    :param mapping_key: source of destination
    :param new_values: Dictionary with key and values to be updated
    :return: updated schema
    """
    for i, mapping_dict in enumerate(schema['mappings']):
        for key in mapping_dict:
            if key in mapping_key:
                if mapping_dict[key]['name'] == name:
                    mapping_dict[key].update(new_values)
                    # print(schema['mappings'][i])
    return schema

