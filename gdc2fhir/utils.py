import json


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
                print(f"Error decoding JSON: {e}")

    return extracted_keys_list


JSON_SCHEMA = {
    "version": "",
    "metadata": {
        "name": "",
        "category": "",
        "description": "",
        "versions": [{"source_version": ""}, {"destination_version": ""}],
        "resource_links": []
    },
    "obj_keys": [],
    "mappings": []
}

PROJECT_MAPPING_TEMPLATE = {
    "source": {
        "name": "",
        "url": "",
        "definition": "",
        "definition_url": "",
        "category": "",
        "type": "",
        "structure": "",
        "has_parent": True,
        "content_annotations": [
            {
                "value": "",
                "annotation_type": "",
                "annotation_url": ""
            }
        ]
    },
    "destination": {
        "name": "",
        "url": "",
        "definition": "",
        "definition_url": "",
        "module": "",
        "type": "",
        "structure": "",
        "has_parent": True
    }
}

CASE_MAPPING_TEMPLATE = {
    "source": {
        "name": "",
        "url": "",
        "definition": "",
        "definition_url": "",
        "category": "",
        "type": "",
        "structure": "",
        "has_parent": True,
        "content_annotations": [
            {
                "value": "",
                "annotation_type": "",
                "annotation_url": ""
            }
        ]
    },
    "destination": {
        "name": "",
        "url": "",
        "definition": "",
        "definition_url": "",
        "module": "",
        "type": "",
        "structure": "",
        "has_parent": True
    }
}


def create_mapping(mapping_template, key, has_parent=True):
    """
    Creates a new mapping based on the provided template and modifies it via parameters passed

    :param mapping_template: Template for the mapping structure
    :param key: Source key to be used in mapping
    :param has_parent: Boolean indicating whether key has a parent. Default is true
    :return: Modified mapping template
    """
    mapping = mapping_template.copy()
    mapping["source"]["name"] = key
    mapping["source"]["has_parent"] = has_parent
    return mapping


def initialize_json_schema(keys, mapping_template, out_path, has_parent=True, source_version="", destination_version="", json_schema=JSON_SCHEMA,
                           json_schema_version="1.0.0"):
    """
    Generates an empty schema json file with all source keys of interest to be mapped to destination keys.

    :param keys: List of keys to be included
    :param mapping_template: A template for mapping ex. GDC case or project
    :param out_path: Path to save json schema
    :param has_parent: Boolean indicating whether key has a parent. Default is true
    :param source_version: Version of source data dictionary
    :param destination_version: Version of destination data dictionary
    :param json_schema: Json schema template
    :param json_schema_version: Version of this json schema template Default is 1.0.0 and follows semantic versioning.
    :return: Initial empty schema json file with all source keys to be mapped
    """

    mappings = [create_mapping(mapping_template, key, has_parent) for key in keys]

    json_schema["version"] = json_schema_version
    json_schema["metadata"]["versions"][0]["source_version"] = source_version
    json_schema["metadata"]["versions"][1]["destination_version"] = destination_version
    json_schema["obj_keys"] = keys
    json_schema["mappings"] = mappings

    json_output = json.dumps(json_schema, indent=4)

    try:
        json.loads(json_output)
    except json.JSONDecodeError as e:
        print(f"JSON is not valid. Error: {e}")

    with open(out_path, "w") as output_file:
        output_file.write(json_output)

