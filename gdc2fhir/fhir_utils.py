import json
import requests
from bs4 import BeautifulSoup

# https://pypi.org/project/fhir.resources/ version 7.1.0 uses FHIR® (Release R5, version 5.0.0)
version = "5.0.0"


def clean_description(description):
    """
    top level description regex cleanup

    :param description: fhir class description txt
    :return: cleaned description txt
    """
    return description.replace("Disclaimer: Any field name ends with ``__ext`` doesn't part of\nResource StructureDefinition, instead used to enable Extensibility feature\nfor FHIR Primitive Data Types.\n\n", "")


def get_us_core(path=None, url=None, param={}):
    """
    Given a path or url to FHIR Extension.extension:[x] loads in data to map to :[x]

    :param param: Json dictionary
    :param path: Path to json
    :param url: url ex. https://build.fhir.org/ig/HL7/US-Core/StructureDefinition-us-core-ethnicity.json
    :return: TBD
    """

    if path:
        with open(path, 'r') as file:
            for line in file:
                try:
                    json_data = json.loads(line)
                    return json_data
                except json.JSONDecodeError as e:
                    print("Error decoding JSON: {}".format(e))
    elif url:
        response = requests.get(url, param=param)

        if response.status_code == 200:
            html_content = response.content.decode("utf-8")
            soup = BeautifulSoup(html_content, 'lxml')
            return soup
    else:
        pass


def is_camel_case(name):
    """
    If the first letter of a word/key is camel case

    :param name: Name of FHIR module/property
    :return: boolean if name is not none and if it's first letter is uppercase
    """
    return name and name[0].isupper()


def decipher_relation(key_name_relation):
    """
    Splits key names by dot notation convention

    :param key_name_relation: string for the distination key name
    :return: list of key names
    """
    names = key_name_relation.split(".")
    return [is_camel_case(n) for n in names]


def has_extension(name):
    """
    Returns true if ':' exists in FHIR naming key convention

    :param name: key name
    :return: bool
    """
    return ":" in name


def schema_enum_reference_types(schem_properties):
    """
    Extracts all enum_reference_types from a FHIR schema property

    :param schem_properties: FHIR schema property
    :return: dictionary of property keys and list of module/nodes they reference to
    """
    d = {}
    for k, v in schem_properties.items():
        if "enum_reference_types" in v.keys():
            d.update({k: v["enum_reference_types"]})
    return d


def schema_element_required(schema_properties):
    """
    Extract element_required from a FHIR schema property and destination keys required

    :param schema_properties:
    :return:
    """
    d = {}
    for k, v in schema_properties.items():
        if "element_required" in v.keys():
            d.update({k: v["element_required"]})
    return d


def append_required_fhir_keys(element_required, required_keys):
    """
    Appends required keys to list of it doesn't exist in list

    :param element_required: dictionary of required elements of a schema property
    :param required_keys: list holding required keys dictionary
    :return: updated required key list
    """
    return [required_keys.append(obj) for obj in element_required if obj not in required_keys]
