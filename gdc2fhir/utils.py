import os
import json
import glob
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from gdc2fhir.schema import Schema, Map

here = os.path.abspath(os.path.dirname(__file__))


def extract_keys(data, parent_key=None, seen_keys=None):
    """
    Extracts all keys in a nested dictionary and applies dot notation to capture nested keys hierarchy.

    ex run:
    data = {
        'a': {
            'b': {
                'c': 1,
                'd': [2, 3]
            }
        },
        'e': [4, 5]
    }

    list(extract_keys(data))
    ['a', 'a.b', 'a.b.c', 'a.b.d', 'e']

    :param data: Resource dictionary containing nested dictionaries hierarchy.
    :param parent_key: Parent key to build the hierarchy.
    :param seen_keys: Set to keep track of seen keys.
    :return: Generator list of hierarchy keys with dot notation.
    """
    if seen_keys is None:
        seen_keys = set()

    if isinstance(data, (dict, list)):
        for k, val in (data.items() if isinstance(data, dict) else enumerate(data)):
            current_key = k if parent_key is None else ".".join([parent_key, k]) if isinstance(data,
                                                                                               dict) else f"{parent_key}"
            if current_key not in seen_keys:
                seen_keys.add(current_key)
                yield current_key
            yield from extract_keys(val, parent_key=current_key, seen_keys=seen_keys)


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


def _read_json(path):
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


# --------------------------------------------------------------------------
# GDC Utility functions
# --------------------------------------------------------------------------


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


def gdc_available_fields(save=True):
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
        annotation_fields = get_field_text(field_tables[3])
        convention_supplement = get_field_text(field_tables[8])  # make dict
        fields = {"project_fields": project_fields, "case_fields": case_fields, "file_fields": file_fields,
                  "annotation_fields": annotation_fields, "convention_supplement": convention_supplement}
        if save:
            for k, v in fields.items():
                jr = json.dumps(v, indent=4)
                out_path = "".join(["./resources/gdc_resources/fields/", k, ".json"])
                with open(out_path, "w") as output_file:
                    output_file.write(jr)
        return fields
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


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


def gdc_api_version_data_info(api_version="v0"):
    api_url = f"https://api.gdc.cancer.gov/{api_version}/status"
    response = requests.get(api_url)

    if response.status_code == 200:
        version_dict = response.json()
        version_dict['source_version'] = version_dict.pop('version')
        return version_dict


def generate_gdc_data_dictionary(create=False):
    """
    saves GDC data dictionary json files via https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?_top=1
    in repo
    """
    # not_listed on https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?_top=1
    file_gdd = gdc_data_dict("file")
    file = {"file": file_gdd}

    # case
    case_gdd = gdc_data_dict("case")
    case = {"case": case_gdd}

    # annotations
    annotation_gdd = gdc_data_dict("annotation")
    annotations = {"annotation": annotation_gdd}

    # administrative
    center_gdd = gdc_data_dict("center")
    project_gdd = gdc_data_dict("project")
    program_gdd = gdc_data_dict("program")
    tissue_source_site_gdd = gdc_data_dict("tissue_source_site")
    administrative = {"center": center_gdd, "project": project_gdd, "program": program_gdd,
                      "tissue_source_site": tissue_source_site_gdd}

    # clinical
    demographic_gdd = gdc_data_dict("demographic")
    diagnosis_gdd = gdc_data_dict("diagnosis")
    exposure_gdd = gdc_data_dict("exposure")
    family_history_gdd = gdc_data_dict("family_history")
    follow_up_gdd = gdc_data_dict("follow_up")
    molecular_test_gdd = gdc_data_dict("molecular_test")
    other_clinical_attribute_gdd = gdc_data_dict("other_clinical_attribute")
    pathology_detail_gdd = gdc_data_dict("pathology_detail")
    treatment_gdd = gdc_data_dict("treatment")
    clinical = {"demographic": demographic_gdd, "diagnosis": diagnosis_gdd, "exposure": exposure_gdd,
                "family_history": family_history_gdd, "follow_up": follow_up_gdd, "molecular_test": molecular_test_gdd,
                "other_clinical_attribute": other_clinical_attribute_gdd, "pathology_detail": pathology_detail_gdd,
                "treatment": treatment_gdd}

    # biospecimen
    slide_gdd = gdc_data_dict("slide")
    sample_gdd = gdc_data_dict("sample")
    read_group_gdd = gdc_data_dict("read_group")
    portion_gdd = gdc_data_dict("portion")
    analyte_gdd = gdc_data_dict("analyte")
    aliquot_gdd = gdc_data_dict("aliquot")
    biospecimen = {"slide": slide_gdd, "sample": sample_gdd, "read_group": read_group_gdd, "portion": portion_gdd,
                   "analyte": analyte_gdd, "aliquot": aliquot_gdd}

    # submittable data files
    analysis_metadata_gdd = gdc_data_dict("analysis_metadata")
    biospecimen_supplement_gdd = gdc_data_dict("biospecimen_supplement")
    clinical_supplement_gdd = gdc_data_dict("clinical_supplement")
    experiment_metadata_gdd = gdc_data_dict("experiment_metadata")
    pathology_report_gdd = gdc_data_dict("pathology_report")
    protein_expression_gdd = gdc_data_dict("protein_expression")
    raw_methylation_array_gdd = gdc_data_dict("raw_methylation_array")
    run_metadata_gdd = gdc_data_dict("run_metadata")
    slide_image_gdd = gdc_data_dict("slide_image")
    submitted_aligned_reads_gdd = gdc_data_dict("submitted_aligned_reads")
    submitted_genomic_profile_gdd = gdc_data_dict("submitted_genomic_profile")
    submitted_genotyping_array_gdd = gdc_data_dict("submitted_genotyping_array")
    submitted_tangent_copy_number_gdd = gdc_data_dict("submitted_tangent_copy_number")
    submitted_unaligned_reads_gdd = gdc_data_dict("submitted_unaligned_reads")
    submittable_data_files = {"analysis_metadata": analysis_metadata_gdd,
                              "biospecimen_supplement": biospecimen_supplement_gdd,
                              "clinical_supplement": clinical_supplement_gdd,
                              "experiment_metadata": experiment_metadata_gdd,
                              "pathology_report": pathology_report_gdd, "protein_expression": protein_expression_gdd,
                              "raw_methylation_array": raw_methylation_array_gdd, "run_metadata": run_metadata_gdd,
                              "slide_image": slide_image_gdd, "submitted_aligned_reads": submitted_aligned_reads_gdd,
                              "submitted_genomic_profile": submitted_genomic_profile_gdd,
                              "submitted_genotyping_array": submitted_genotyping_array_gdd,
                              "submitted_tangent_copy_number": submitted_tangent_copy_number_gdd,
                              "submitted_unaligned_reads": submitted_unaligned_reads_gdd}

    # generated data files
    aggregated_somatic_mutation_gdd = gdc_data_dict("aggregated_somatic_mutation")
    aligned_reads_gdd = gdc_data_dict("aligned_reads")
    annotated_somatic_mutation_gdd = gdc_data_dict("annotated_somatic_mutation")
    copy_number_auxiliary_file_gdd = gdc_data_dict("copy_number_auxiliary_file")
    copy_number_estimate_gdd = gdc_data_dict("copy_number_estimate")
    copy_number_segment_gdd = gdc_data_dict("copy_number_segment")
    filtered_copy_number_segment_gdd = gdc_data_dict("filtered_copy_number_segment")
    gene_expression_gdd = gdc_data_dict("gene_expression")
    masked_methylation_array_gdd = gdc_data_dict("masked_methylation_array")
    masked_somatic_mutation_gdd = gdc_data_dict("masked_somatic_mutation")
    methylation_beta_value_gdd = gdc_data_dict("methylation_beta_value")
    mirna_expression_gdd = gdc_data_dict("mirna_expression")
    secondary_expression_analysis_gdd = gdc_data_dict("secondary_expression_analysis")
    simple_germline_variation_gdd = gdc_data_dict("simple_germline_variation")
    simple_somatic_mutation_gdd = gdc_data_dict("simple_somatic_mutation")
    structural_variation_gdd = gdc_data_dict("structural_variation")
    generated_data_files = {"aggregated_somatic_mutation": aggregated_somatic_mutation_gdd,
                            "aligned_reads": aligned_reads_gdd,
                            "annotated_somatic_mutation": annotated_somatic_mutation_gdd,
                            "copy_number_auxiliary_file": copy_number_auxiliary_file_gdd,
                            "copy_number_estimate": copy_number_estimate_gdd,
                            "copy_number_segment": copy_number_segment_gdd,
                            "filtered_copy_number_segment": filtered_copy_number_segment_gdd,
                            "gene_expression": gene_expression_gdd,
                            "masked_methylation_array": masked_methylation_array_gdd,
                            "masked_somatic_mutation": masked_somatic_mutation_gdd,
                            "methylation_beta_value": methylation_beta_value_gdd,
                            "mirna_expression": mirna_expression_gdd,
                            "secondary_expression_analysis": secondary_expression_analysis_gdd,
                            "simple_germline_variation": simple_germline_variation_gdd,
                            "simple_somatic_mutation": simple_somatic_mutation_gdd,
                            "structural_variation": structural_variation_gdd}

    # analysis
    alignment_cocleaning_workflow_gdd = gdc_data_dict("alignment_cocleaning_workflow")
    alignment_workflow_gdd = gdc_data_dict("alignment_workflow")
    copy_number_liftover_workflow_gdd = gdc_data_dict("copy_number_liftover_workflow")
    copy_number_variation_workflow_gdd = gdc_data_dict("copy_number_variation_workflow")
    expression_analysis_workflow_gdd = gdc_data_dict("expression_analysis_workflow")
    genomic_profile_harmonization_workflow_gdd = gdc_data_dict("genomic_profile_harmonization_workflow")
    germline_mutation_calling_workflow_gdd = gdc_data_dict("germline_mutation_calling_workflow")
    methylation_array_harmonization_workflow_gdd = gdc_data_dict("methylation_array_harmonization_workflow")
    methylation_liftover_workflow_gdd = gdc_data_dict("methylation_liftover_workflow")
    mirna_expression_workflow_gdd = gdc_data_dict("mirna_expression_workflow")
    rna_expression_workflow_gdd = gdc_data_dict("rna_expression_workflow")
    somatic_aggregation_workflow_gdd = gdc_data_dict("somatic_aggregation_workflow")
    somatic_annotation_workflow_gdd = gdc_data_dict("somatic_annotation_workflow")
    somatic_copy_number_workflow_gdd = gdc_data_dict("somatic_copy_number_workflow")
    somatic_mutation_calling_workflow_gdd = gdc_data_dict("somatic_mutation_calling_workflow")
    structural_variant_calling_workflow_gdd = gdc_data_dict("structural_variant_calling_workflow")
    analysis = {"alignment_cocleaning_workflow": alignment_cocleaning_workflow_gdd,
                "alignment_workflow": alignment_workflow_gdd,
                "copy_number_liftover_workflow": copy_number_liftover_workflow_gdd,
                "copy_number_variation_workflow": copy_number_variation_workflow_gdd,
                "expression_analysis_workflow": expression_analysis_workflow_gdd,
                "genomic_profile_harmonization_workflow": genomic_profile_harmonization_workflow_gdd,
                "germline_mutation_calling_workflow": germline_mutation_calling_workflow_gdd,
                "methylation_array_harmonization_workflow": methylation_array_harmonization_workflow_gdd,
                "methylation_liftover_workflow": methylation_liftover_workflow_gdd,
                "mirna_expression_workflow": mirna_expression_workflow_gdd,
                "rna_expression_workflow": rna_expression_workflow_gdd,
                "somatic_aggregation_workflow": somatic_aggregation_workflow_gdd,
                "somatic_annotation_workflow": somatic_annotation_workflow_gdd,
                "somatic_copy_number_workflow": somatic_copy_number_workflow_gdd,
                "somatic_mutation_calling_workflow": somatic_mutation_calling_workflow_gdd,
                "structural_variant_calling_workflow": structural_variant_calling_workflow_gdd}

    # notation
    read_group_qc_gdd = gdc_data_dict("read_group_qc")
    notation = {"read_group_qc": read_group_qc_gdd}

    # index
    aligned_reads_index_gdd = gdc_data_dict("aligned_reads_index")
    somatic_mutation_gdd = gdc_data_dict("somatic_mutation_index")
    index = {"aligned_reads_index": aligned_reads_index_gdd, "somatic_mutation_index": somatic_mutation_gdd}

    # data
    data_release_gdd = gdc_data_dict("data_release")
    root_gdd = gdc_data_dict("root")
    data = {"data_release": data_release_gdd, "root": root_gdd}

    names = ["file", "case", "annotations", "administrative", "clinical", "biospecimen", "submittable_data_files",
             "generated_data_files", "analysis", "notation", "index", "data"]
    dict_list = [file, case, annotations, administrative, clinical, biospecimen, submittable_data_files,
                 generated_data_files,
                 analysis, notation, index, data]

    for i, d in enumerate(dict_list):
        dir = "".join(["./resources/gdc_resources/data_dictionary/", names[i]])
        if not os.path.exists(dir) and create:
            os.makedirs(dir)
        for k, v, in d.items():
            path = "".join([dir, "/", k, ".json"])
            with open(path, "w") as output_file:
                output_file.write(json.dumps(v, indent=4))


def load_data_dictionary(path="./resources/gdc_resources/data_dictionary/"):
    """
    Reads in  data_dictionary from file-path hierarchy and creates a dictionary for data mapping

    :param path:  Path string to data_dictionary files "./resources/gdc_resources/data_dictionary"
    :return: Dictionary of GDC data_dictionaries
    """

    all_paths = glob.glob("".join([path, "**/*.json"]))
    all_dat = {}

    for i, item in enumerate(all_paths):
        module_path = all_paths[i].replace(path, "").split("/")
        module = module_path[0]
        if module not in all_dat.keys():
            all_dat.update({module: {}})

        module_file = module_path[1]
        name = module_file.replace(".json", "")
        dat_dict = _read_json(all_paths[i])
        all_dat[module].update({name: dat_dict})

    return all_dat


def load_fields(path="./resources/gdc_resources/fields/"):
    """
    loads GDC fields in resources

    :param path: path to json files
    :return: dictionary with file name and json content value
    """
    all_paths = glob.glob("".join([path, "/*.json"]))
    all_dat = {}

    for i, item in enumerate(all_paths):
        field_path = all_paths[i].replace(path, "").split("/")
        field_file = field_path[0]

        name = field_file.replace(".json", "")
        dat_dict = _read_json(all_paths[i])

        all_dat.update({name: dat_dict})

    return all_dat


# --------------------------------------------------------------------------
# FHIR Utility functions
# --------------------------------------------------------------------------


# https://pypi.org/project/fhir.resources/ version 7.1.0 uses FHIR® (Release R5, version 5.0.0)
version = "5.0.0"


def clean_description(description):
    """
    top level description regex cleanup

    :param description: fhir class description txt
    :return: cleaned description txt
    """
    description = description.replace(
        "Disclaimer: Any field name ends with ``__ext`` doesn't part of\nResource StructureDefinition, instead used to enable Extensibility feature\nfor FHIR Primitive Data Types.\n\n",
        "")
    description = description.replace('\n\n', '\n')
    description = description.replace('\n', ' ')
    return description


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


# -------------------------------------------------
# mapping.py utils
# -------------------------------------------------
_data_dict = load_data_dictionary()


def validate_and_write(schema, out_path, update=False, generate=False):
    Schema.model_validate(schema)

    schema_extra = schema.Config.json_schema_extra.get('$schema', None)
    schema_dict = schema.dict()
    schema_dict = {'$schema': schema_extra, **schema_dict}

    if os.path.exists(out_path) and update:
        with open(out_path, 'w') as json_file:
            json.dump(schema_dict, json_file, indent=4)
    elif generate:
        if os.path.exists(out_path):
            print(f"File: {out_path} exists.")
        else:
            with open(out_path, 'w') as json_file:
                json.dump(schema_dict, json_file, indent=4)
    else:
        print(f"File: {out_path} update not required")


def load_schema_from_json(path) -> Schema:
    with open(path, "r") as j:
        data = json.load(j)
        return Schema.parse_obj(data)


def load_gdc_scripts_json(path):
    try:
        with open(path, 'r') as gdc_file:
            content = gdc_file.read()
            obj = [json.loads(obj) for obj in content.strip().split('\n')]
            return obj
    except json.JSONDecodeError as e:
        print(e)


def traverse_and_map(node, current_keys, mapped_data, available_maps, success_counter, verbose=True):
    """
    TODO: initial simple version of mapping - needs checks for hierarchy mapping, parent ref assignemnets, and content annotations
    Traverse a GDC script and map keys from GDC to FHIR based on Schema's Map objects in gdc2fhir labes python definitions

    :param node:
    :param current_keys:
    :param mapped_data:
    :param available_maps:
    :param success_counter:
    :param verbose:
    :return:
    """
    for key, value in node.items():
        current_key = '.'.join(current_keys + [key])
        schema_map = next((m for m in available_maps if m and m.source.name == current_key), None)

        if schema_map:
            # fetch the Map's destination
            destination_key = schema_map.destination.name
            # separate hierarchy key to track
            hierarchy_key = current_keys[0] if current_keys else None

            if verbose:
                print("hierarchy_key: ", hierarchy_key,"\n")

            if hierarchy_key and hierarchy_key not in mapped_data:
                mapped_data[hierarchy_key] = {}

            current_dat = mapped_data
            for nested_key in current_keys:
                if nested_key not in current_dat:
                    # create dict for hierarchy parsing
                    current_dat[nested_key] = {}
                current_dat = current_dat[nested_key]

                if verbose:
                    print("current_dat: ", current_dat, "\n")

            if destination_key not in current_dat:
                # check Map's destination
                current_dat[destination_key] = value

                if verbose:
                    print("assigned destination and it's value: ", current_dat, "\n")

            # successful map counter
            success_counter['mapped'] += 1

        elif isinstance(value, dict):
            if verbose:
                print("instance dict - recall:", current_keys + [key] , "\n")
            traverse_and_map(value, current_keys + [key], mapped_data, available_maps, success_counter, verbose)



def map_data(data, available_maps: List[Optional[Map]], verbose) -> Dict:
    """
    Map GDC keys to FHIR and count successful mappings

    :param data:
    :param available_maps:
    :param verbose:
    :return:
    """

    mapped_data = {}
    success_counter = {'mapped': 0}
    traverse_and_map(data, [], mapped_data, available_maps, success_counter, verbose)
    if verbose:
        print('Available Map items of entity: ', len(available_maps), '\n')
        print('mapped_data: ', mapped_data, '\n\n', f'Mapped {success_counter["mapped"]} key items.', '\n')
    return {'mapped_data': mapped_data, 'success_counter': success_counter['mapped']}

