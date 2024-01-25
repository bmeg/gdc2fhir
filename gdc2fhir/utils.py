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

"""
# TODO: remove use-cases
generate_content_annotations(demographic_dict['properties']['race'], "content_annotations/demographic/race.json")
generate_content_annotations(demographic_dict['properties']['ethnicity'], "content_annotations/demographic/ethnicity.json")
generate_content_annotations(case_dict['properties']['disease_type'], "content_annotations/case/disease_type.json")
generate_content_annotations(case_dict['properties']['primary_site'], "content_annotations/case/primary_site.json")
"""


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
                        print(mapping_dict)
    # return schema


def read_schema(path):
    with open(path, encoding='utf-8') as f:
        entity_schema = json.load(f)
        return entity_schema

# remove after first commit -------
case_schema = read_schema("./mapping/case.json")
file_schema = read_schema("./mapping/file.json")


l = [
        {
            "source": {
                "name": "case_id",
                "url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=case",
                "description": "Unique key of entity",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=case",
                "category": "case",
                "type": "unique key"
            },
            "destination": {
                "name": "Observation.identifier",
                "title": "Business Identifier for observation",
                "description": "A unique identifier assigned to this observation.",
                "description_url": "https://build.fhir.org/observation-definitions.html#Observation.identifier",
                "module": "Diagnostics",
                "type": "Identifier"
            }
        },
        {
            "source": {
                "name": "primary_site",
                "description": "The text term used to describe the primary site of disease, as categorized by the World Health Organization's (WHO) International Classification of Diseases for Oncology (ICD-O). This categorization groups cases into general categories. Reference tissue_or_organ_of_origin on the diagnosis node for more specific primary sites of disease.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/case",
                "category": "case",
                "type": "string",
                "content_annotation": "@content_annotations/case/primary_sites.json"
            },
            "destination": {
                "name": "Observation.bodysite",
                "title": "Observed body part",
                "description": "Indicates the site on the subject's body where the observation was made (i.e. the target site).",
                "description_url": "https://build.fhir.org/observation-definitions.html#Observation.bodySite",
                "module": "Diagnostics",
                "type": "CodeableConcept"
            }
        },
        {
            "source": {
                "name": "demographic.age_at_index",
                "description": "The patient's age (in years) on the reference or anchor date used during date obfuscation.",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=demographic&anchor=age_at_index",
                "category": "clinical",
                "type": "integer"
            },
            "destination": {
                "name": "Patient.Extension.valueInteger",
                "title": "Value of extension",
                "description": "Value of extension - must be one of a constrained set of the data types (see [Extensibility](extensibility.html) for a list).",
                "description_url": "https://www.hl7.org/fhir/extensibility-definitions.html#Extension.value_x_",
                "module": "Foundation",
                "type": "integer"
            }
        },
        {
            "source": {
                "name": "demographic.days_to_birth",
                "description": "Number of days between the date used for index and the date from a person's date of birth represented as a calculated negative number of days.",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=demographic&anchor=days_to_birth",
                "category": "clinical",
                "type": "integer"
            },
            "destination": {
                "name": "Patient.Extension.valueInteger",
                "title": "Value of extension",
                "description": "Value of extension - must be one of a constrained set of the data types (see [Extensibility](extensibility.html) for a list).",
                "description_url": "https://www.hl7.org/fhir/extensibility-definitions.html#Extension.value_x_",
                "module": "Foundation",
                "type": "integer"
            }
        },
        {
            "source": {
                "name": "project.name",
                "description": "Display name for the project",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/project",
                "category": "administrative",
                "type": "string"
            },
            "destination": {
                "name": "ResearchStudy.name",
                "title": "Name for this study (computer friendly)",
                "description": "Name for this study (computer friendly).",
                "description_url": "https://build.fhir.org/researchstudy-definitions.html#ResearchStudy.name",
                "module": "Administration",
                "type": "string"
            }
        },
        {
            "source": {
                "name": "project.program.dbgap_accession_number",
                "description": "The dbgap accession number provided for the program.",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=program&anchor=dbgap_accession_number",
                "category": "administrative",
                "type": "string"
            },
            "destination": {
                "name": "ResearchStudy.ResearchStudy.partOf.Coding.code",
                "title": "Symbol in syntax defined by the system",
                "description": "A symbol in syntax defined by the system. The symbol may be a predefined code or an expression in a syntax defined by the coding system (e.g. post-coordination).",
                "description_url": "https://build.fhir.org/datatypes-definitions.html",
                "module": "DataTypes",
                "type": "string"
            }
        },
        {
            "source": {
                "name": "demographic.submitter_id",
                "description": "A project-specific identifier for a node. This property is the calling card/nickname/alias for a unit of submission. It can be used in place of the uuid for identifying or recalling a node.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/demographic",
                "category": "clinical",
                "type": "string"
            },
            "destination": {
                "name": "ResearchSubject.identifier",
                "title": "Business Identifier for research subject in a study",
                "description": "Identifiers assigned to this research subject for a study.",
                "description_url": "https://build.fhir.org/researchsubject-definitions.html#ResearchSubject.identifier",
                "module": "Administration",
                "type": "code"
            }
        },
        {
            "source": {
                "name": "project.primary_site",
                "description": "The text term used to describe the primary site of disease, as categorized by the World Health Organization's (WHO) International Classification of Diseases for Oncology (ICD-O). This categorization groups cases into general categories. Reference tissue_or_organ_of_origin on the diagnosis node for more specific primary sites of disease.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/case",
                "category": "administrative",
                "type": "string",
                "content_annotation": "@content_annotations/case/primary_sites.json"
            },
            "destination": {
                "name": "ResearchStudy.Observation.bodySite",
                "title": "Observed body part",
                "description": "Indicates the body structure on the subject's body where the observation was made (i.e. the target site).",
                "description_url": "https://build.fhir.org/observation-definitions.html#Observation.bodySite",
                "module": "Diagnostics",
                "type": "CodeableConcept"
            }
        },
        {
            "source": {
                "name": "sample_ids",
                "description": "list of sample ids - A 128-bit identifier. Depending on the mechanism used to generate it, it is either guaranteed to be different from all other UUIDs/GUIDs generated until 3400 AD or extremely likely to be different. Its relatively small size lends itself well to sorting, ordering, and hashing of all sorts, storing in databases, simple allocation, and ease of programming in general.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/sample",
                "category": "biospecimen",
                "type": "string"
            },
            "destination": {
                "name": "Specimen.identifier",
                "title": "External Identifier",
                "description": "Id for specimen.",
                "description_url": "https://build.fhir.org/specimen-definitions.html#Specimen.identifier",
                "module": "Diagnostics",
                "type": "Identifier"
            }
        },
        {
            "source": {
                "name": "samples",
                "description": "List of samples - Any material sample taken from a biological entity for testing, diagnostic, propagation, treatment or research purposes, including a sample obtained from a living organism or taken from the biological object after halting of all its life functions. Biospecimen can contain one or more components including but not limited to cellular molecules, cells, tissues, organs, body fluids, embryos, and body excretory products.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/sample",
                "category": "biospecimen",
                "type": "object"
            },
            "destination": {
                "name": "Specimen",
                "title": "Specimen",
                "description": "Sample for analysis. A sample to be used for analysis.",
                "description_url": "https://build.fhir.org/specimen-definitions.html#Specimen",
                "module": "Diagnostics",
                "type": "DomainResource"
            }
        },
        {
            "source": {
                "name": "exposures",
                "description": "Clinically relevant patient information not immediately resulting from genetic predispositions.",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=exposure",
                "category": "clinical",
                "type": "object"
            },
            "destination": {
                "name": "ObservationDefinition",
                "title": "ObservationDefinition",
                "description": "Set of definitional characteristics for a kind of observation or measurement produced or consumed by an orderable health care service.",
                "description_url": "https://build.fhir.org/observationdefinition-definitions.html#ObservationDefinition",
                "module": "Administration",
                "type": "MetadataResource"
            }
        },
        {
            "source": {
                "name": "index_date",
                "description": "The text term used to describe the reference or anchor date used when for date obfuscation, where a single date is obscurred by creating one or more date ranges in relation to this date.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/case",
                "category": "case",
                "type": "string",
                "enum": [
                    "Diagnosis",
                    "First Patient Visit",
                    "First Treatment",
                    "Initial Genomic Sequencing",
                    "Recurrence",
                    "Sample Procurement",
                    "Study Enrollment"
                    ]
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
        {
            "source": {
                "name": "demographic.year_of_birth",
                "description": "Numeric value to represent the calendar year in which an individual was born.",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=demographic&anchor=year_of_birth",
                "category": "clinical",
                "type": "integer"
            },
            "destination": {
                "name": "Patient.birthDate",
                "title": "The date of birth for the individual",
                "description": "The date of birth for the individual",
                "description_url": "https://www.hl7.org/fhir/patient-definitions.html#Patient.birthDate",
                "module": "Administration",
                "type": "date"
            }
        },
        {
            "source": {
                "name": "demographic",
                "description": "Data for the characterization of the patient by means of segmenting the population (e.g., characterization by age, sex, or race).",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=demographic",
                "category": "clinical",
                "type": "object"
            },
            "destination": {
                "name": "Patient",
                "title": "Patient",
                "description": "Demographics and other administrative information about an individual or animal receiving care or other health-related services.",
                "description_url": "https://build.fhir.org/patient-definitions.html",
                "module": "Administration",
                "type": "DomainResource"
            }
        },
        {
            "source": {
                "name": "project.disease_type",
                "description": "The text term used to describe the type of malignant disease, as categorized by the World Health Organization's (WHO) International Classification of Diseases for Oncology (ICD-O)",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/case",
                "category": "case",
                "type": "string",
                "content_annotation": "@content_annotations/case/disease_types.json"
            },
            "destination": {
                "name": "ResearchStudy.condition",
                "title": "Condition being studied",
                "description": "The condition that is the focus of the study. For example, In a study to examine risk factors for Lupus, might have as an inclusion criterion \"healthy volunteer\", but the target condition code would be a Lupus SNOMED code.",
                "description_url": "https://build.fhir.org/researchstudy-definitions.html#ResearchStudy.condition",
                "module": "Administration",
                "type": "CodeableConcept"
            }
        },
        {
            "source": {
                "name": "demographic.race",
                "description": "An arbitrary classification of a taxonomic group that is a division of a species. It usually arises as a consequence of geographical isolation within a species and is characterized by shared heredity, physical attributes and behavior, and in the case of humans, by common history, nationality, or geographic distribution. The provided values are based on the categories defined by the U.S. Office of Management and Business and used by the U.S. Census Bureau.",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=demographic&anchor=race",
                "category": "clinical",
                "type": "Race Category Text",
                "content_annotation": "@content_annotations/demographic/race.json"
            },
            "destination": {
                "name": "Patient.Extension.extension:USCoreRaceExtension",
                "title": "'Additional content defined by implementations",
                "description": "Concepts classifying the person into a named category of humans sharing common history, traits, geographical origin or nationality. The race codes used to represent these concepts are based upon the CDC Race and Ethnicity Code Set Version 1.0 which includes over 900 concepts for representing race and ethnicity of which 921 reference race. The race concepts are grouped by and pre-mapped to the 5 OMB race categories.",
                "description_url": "http://hl7.org/fhir/us/core/STU6.1/StructureDefinition-us-core-race-definitions.html#diff_Extension",
                "module": "Extension",
                "type": "Extension"
            }
        },
        {
            "source": {
                "name": "disease_type",
                "description": "The text term used to describe the type of malignant disease, as categorized by the World Health Organization's (WHO) International Classification of Diseases for Oncology (ICD-O).",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=case",
                "category": "case",
                "type": "string",
                "content_annotation": "@content_annotations/case/disease_types.json"
            },
            "destination": {
                "name": "ResearchStudy.condition",
                "title": "Condition being studied",
                "description": "The condition that is the focus of the study. For example, In a study to examine risk factors for Lupus, might have as an inclusion criterion \"healthy volunteer\", but the target condition code would be a Lupus SNOMED code.",
                "description_url": "https://build.fhir.org/researchstudy-definitions.html#ResearchStudy.condition",
                "module": "Administration",
                "type": "CodeableConcept"
            }
        },
        {
            "source": {
                "name": "project.program.name",
                "description": "Full name/title of the program.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/program",
                "category": "administrative",
                "type": "string"
            },
            "destination": {
                "name": "ResearchStudy.ResearchStudy.partOf.name",
                "title": "Name for this study (computer friendly).",
                "description": "Name for this study (computer friendly).",
                "description_url": "https://build.fhir.org/researchstudy-definitions.html#ResearchStudy.name",
                "module": "Administration",
                "type": "string"
            }
        },
        {
            "source": {
                "name": "tissue_source_site",
                "description": "A clinical site that collects and provides patient samples and clinical metadata for research use. (NCIt C103264)",
                "description_url": "https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=tissue_source_site",
                "category": "administrative",
                "type": "object"
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
        {
            "source": {
                "name": "demographic.ethnicity",
                "description": "An individual's self-described social and cultural grouping, specifically whether an individual describes themselves as Hispanic or Latino. The provided values are based on the categories defined by the U.S. Office of Management and Business and used by the U.S. Census Bureau.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/demographic",
                "category": "clinical",
                "type": "Ethnic Group Category Text",
                "content_annotation": "@content_annotations/demographic/ethnicity.json"
            },
            "destination": {
                "name": "Patient.Extension:extension.USCoreEthnicity",
                "title": "Additional content defined by implementations",
                "description": "Concepts classifying the person into a named category of humans sharing common history, traits, geographical origin or nationality. The race codes used to represent these concepts are based upon the CDC Race and Ethnicity Code Set Version 1.0 which includes over 900 concepts for representing race and ethnicity of which 921 reference race. The race concepts are grouped by and pre-mapped to the 5 OMB race categories.",
                "description_url": "https://build.fhir.org/ig/HL7/US-Core/StructureDefinition-us-core-ethnicity.profile.json.html",
                "module": "Extension",
                "type": "Extension"
            }
        }
    ]

l = [
        {
            "source": {
                "name": "id",
                "url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "description": "Universally Unique Identifier",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "category": "data_file",
                "type": "string"
            },
            "destination": {
                "name": "DocumentReference.identifier",
                "title": "Business identifiers for the document",
                "url": "https://build.fhir.org/documentreference-definitions.html#DocumentReference.identifier",
                "description": "Business identifiers assigned to this document reference by the performer and/or other systems. These identifiers remain constant as the resource is updated and propagates from server to server.",
                "description_url": "https://build.fhir.org/documentreference-definitions.html#DocumentReference.identifier",
                "module": "Diagnostics",
                "type": "Identifier"
            }
        },
        {
            "source": {
                "name": "submitter_id",
                "url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "description": "A project-specific identifier for a node. This property is the calling card/nickname/alias for a unit of submission. It can be used in place of the uuid for identifying or recalling a node.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "category": "data_file",
                "type": "string"
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
        {
            "source": {
                "name": "file_name",
                "url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "description": "The name (or part of a name) of a file (of any type).",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "category": "data_file",
                "type": "string"
            },
            "destination": {
                "name": "DocumentReference.content.Attachment.title",
                "title": "Label to display in place of the data",
                "url": "",
                "description": "A label or set of text to display in place of the data.",
                "description_url": "",
                "module": "Attachment",
                "type": "string"
            }
        },
        {
            "source": {
                "name": "file_size",
                "url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "description": "The size of the data file (object) in bytes.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "category": "data_file",
                "type": "integer"
            },
            "destination": {
                "name": "DocumentReference.content.Attachment.size",
                "title": "Number of bytes of content (if url provided)",
                "url": "https://build.fhir.org/documentreference-definitions.html#DocumentReference.content.attachment",
                "description": "The number of bytes of data that make up this attachment (before base64 encoding, if that is done).",
                "description_url": "https://build.fhir.org/datatypes-definitions.html#Attachment.size",
                "module": "Attachment",
                "type": "integer64"
            }
        },
        {
            "source": {
                "name": "md5sum",
                "url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "description": "The 128-bit hash value expressed as a 32 digit hexadecimal number (in lower case) used as a file's digital fingerprint.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "category": "data_file",
                "type": "string"
            },
            "destination": {
                "name": "Extension.valueString",
                "title": "Value of extension",
                "url": "https://www.hl7.org/fhir/extensibility-definitions.html#Extension.value_x_",
                "description": "Value of extension - must be one of a constrained set of the data types (see [Extensibility](extensibility.html) for a list).",
                "description_url": "https://www.hl7.org/fhir/extensibility-definitions.html#Extension.value_x_",
                "module": "Extensibility",
                "type": "string"
            }
        },
        {
            "source": {
                "name": "state",
                "url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "description": "The current state of the object.",
                "description_url": "https://api.gdc.cancer.gov/v0/submission/_dictionary/file",
                "category": "data_file",
                "type": "string"
            },
            "destination": {
                "name": "DocumentReference.status",
                "title": "current | superseded | entered-in-error",
                "url": "https://build.fhir.org/documentreference-definitions.html#DocumentReference.status",
                "description": "The status of this document reference.",
                "description_url": "https://build.fhir.org/documentreference-definitions.html#DocumentReference.status",
                "module": "Diagnostics",
                "type": "code"
            }
        }
    ]

source_names = []
for d in l:
    source_names.append(d['source']['name'])

for d in l:
    update_values(file_schema, source_name=d['source']['name'], source=True, destination=True, source_values=d['source'], destination_values=d['destination'])

with open("mapping/file.json", 'w', encoding='utf-8') as file:
    json.dump(file_schema, file, indent=4)


