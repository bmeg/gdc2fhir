import json
from typing import List, Optional
from gdc2fhir.schema import Schema, Source, Destination, Map, Metadata, JsonMeta, Version


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


def initialize_content_annotations(annot_enum, out_path):
    """
    Generates the initial list dictionary of content annotations to annotate

    :param annot_enum: List of annotations strings
    :param out_path: File path for the generated JSON.
    :return: List of dictionaries with each content annotation name as value's key
    """
    obj_list = []
    if isinstance(annot_enum, dict):
        for k, v in annot_enum.items():
            content_annotation = {
                "value": k,
                "description": v["description"],
                "description_url": v["termDef"]["term_url"],
                "annotation_type": v["termDef"]["source"]
                # "ontology_url": "",
                # "sctid": ""
            }
            obj_list.append(content_annotation)

    if isinstance(annot_enum, list):
        for item in annot_enum:
            content_annotation = {
                "value": item,
                "description": "",
                "description_url": "",
                "annotation_type": ""
                # "ontology_url": "",
                # "sctid": ""
            }
            obj_list.append(content_annotation)

    jr = json.dumps(obj_list, indent=4)

    if out_path:
        with open(out_path, "w") as output_file:
            output_file.write(jr)


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


def update_values(schema, source_name, source=True, destination=False, source_values=None, destination_values=None):
    """
    Updates values of source and/or destination keys

    :param schema: Json schema to be updated
    :param source_name: name of source to be updated
    :param source: boolean indicating source to be updated
    :param destination: boolean indicating destination to be updated
    :param source_values: Dictionary with updated info
    :param destination_values: Dictionary with updated info
    :return: updated schema
    """
    for i, mapping_dict in enumerate(schema['mappings']):
        for key in mapping_dict:
            if key == "source" and source:
                if mapping_dict[key]['name'] == source_name:
                    mapping_dict[key].update(source_values)
                    if destination:
                        mapping_dict['destination'].update(destination_values)


def read_json(path):
    """
    Reads in json file

    :param path: path to json file
    :return:
    """
    try:
        with open(path, encoding='utf-8') as f:
            this_json = json.load(f)
            return this_json
    except json.JSONDecodeError as e:
        print("Error decoding JSON: {}".format(e))

