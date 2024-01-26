import os
import json
import requests
from bs4 import BeautifulSoup


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
    submittable_data_files = {"analysis_metadata": analysis_metadata_gdd, "biospecimen_supplement": biospecimen_supplement_gdd,
                              "clinical_supplement": clinical_supplement_gdd, "experiment_metadata": experiment_metadata_gdd,
                              "pathology_report": pathology_report_gdd, "protein_expression": protein_expression_gdd,
                              "raw_methylation_array": raw_methylation_array_gdd, "run_metadata": run_metadata_gdd,
                              "slide_image": slide_image_gdd, "submitted_aligned_reads": submitted_aligned_reads_gdd,
                              "submitted_genomic_profile": submitted_genomic_profile_gdd, "submitted_genotyping_array": submitted_genotyping_array_gdd,
                              "submitted_tangent_copy_number": submitted_tangent_copy_number_gdd, "submitted_unaligned_reads": submitted_unaligned_reads_gdd}

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
    generated_data_files = {"aggregated_somatic_mutation": aggregated_somatic_mutation_gdd, "aligned_reads": aligned_reads_gdd,
                            "annotated_somatic_mutation": annotated_somatic_mutation_gdd,
                            "copy_number_auxiliary_file": copy_number_auxiliary_file_gdd, "copy_number_estimate": copy_number_estimate_gdd,
                            "copy_number_segment": copy_number_segment_gdd, "filtered_copy_number_segment": filtered_copy_number_segment_gdd,
                            "gene_expression": gene_expression_gdd, "masked_methylation_array": masked_methylation_array_gdd,
                            "masked_somatic_mutation": masked_somatic_mutation_gdd, "methylation_beta_value": methylation_beta_value_gdd,
                            "mirna_expression": mirna_expression_gdd, "secondary_expression_analysis": secondary_expression_analysis_gdd,
                            "simple_germline_variation": simple_germline_variation_gdd, "simple_somatic_mutation": simple_somatic_mutation_gdd,
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
    analysis = {"alignment_cocleaning_workflow": alignment_cocleaning_workflow_gdd, "alignment_workflow": alignment_workflow_gdd,
                "copy_number_liftover_workflow": copy_number_liftover_workflow_gdd, "copy_number_variation_workflow": copy_number_variation_workflow_gdd,
                "expression_analysis_workflow": expression_analysis_workflow_gdd, "genomic_profile_harmonization_workflow": genomic_profile_harmonization_workflow_gdd,
                "germline_mutation_calling_workflow": germline_mutation_calling_workflow_gdd, "methylation_array_harmonization_workflow": methylation_array_harmonization_workflow_gdd,
                "methylation_liftover_workflow": methylation_liftover_workflow_gdd, "mirna_expression_workflow": mirna_expression_workflow_gdd,
                "rna_expression_workflow": rna_expression_workflow_gdd, "somatic_aggregation_workflow": somatic_aggregation_workflow_gdd,
                "somatic_annotation_workflow": somatic_annotation_workflow_gdd, "somatic_copy_number_workflow": somatic_copy_number_workflow_gdd,
                "somatic_mutation_calling_workflow": somatic_mutation_calling_workflow_gdd, "structural_variant_calling_workflow": structural_variant_calling_workflow_gdd}

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
    dict_list = [file, case, annotations, administrative, clinical, biospecimen, submittable_data_files, generated_data_files,
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
    # glob.glob('./resources/gdc_resources/data_dictionary/**/*.json') # get all
    # os.walk(path) # get hierarchy
    pass


# (load all || point to an existing resource ? if there are any ) && save in repo for versioning
# demographic_dict = gdc_data_dict("demographic")
# project_dict = gdc_data_dict("project")
# case_dict = gdc_data_dict("case")
# file_dict = gdc_data_dict("file")
# annotations_dict = gdc_data_dict("annotations")
# primary_sites = case_dict['properties']['primary_site']['enum']
# disease_types = case_dict['properties']['disease_type']['enum']

