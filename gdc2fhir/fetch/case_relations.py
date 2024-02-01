import os.path
import json
from gdc2fhir import utils, gdc_utils
from fhir.resources.patient import Patient
from fhir.resources.coding import Coding
from fhir.resources.observation import Observation
from fhir.resources.observationdefinition import ObservationDefinition
from fhir.resources.extension import Extension
from fhir.resources.researchstudy import ResearchStudy, ResearchStudyRecruitment, ResearchStudyProgressStatus
from fhir.resources.genomicstudy import GenomicStudyAnalysis
from fhir.resources.researchsubject import ResearchSubject
from fhir.resources.specimen import Specimen
from fhir.resources.imagingstudy import ImagingStudy
from fhir.resources.annotation import Annotation
from fhir.resources.condition import Condition

from fhir.resources.documentreference import DocumentReference
from fhir.resources.attachment import Attachment

# read in schema and update relations
case_schema_path = "./mapping/case.json"
if os.path.isfile(case_schema_path):
    case_schema = utils.read_json(case_schema_path)

# read in GDC fields and data_dictionaries
fields = gdc_utils.load_fields()
data_dict = gdc_utils.load_data_dictionary()
# ------------------------------
name = case_schema['mappings'][0]['source']['name']
print(name)

# aliquot_ids -> specimen.ids
case_mapping = case_schema['mappings'][0]
case_mapping["source"]["description"] = data_dict["biospecimen"]["aliquot"]["properties"]["id"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["aliquot"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["aliquot"]["properties"]["id"]["type"]

case_mapping["destination"]["name"] = "Specimen.identifier"
case_mapping["destination"]["title"] = Specimen.schema()["properties"]["identifier"]["title"]
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["identifier"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["identifier"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ---------------------------------
name = case_schema['mappings'][1]['source']['name']
print(name)

# analyte_ids -> Specimen.identifier
case_mapping = case_schema['mappings'][1]
case_mapping["source"]["description"] = data_dict["biospecimen"]["analyte"]["properties"]["id"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["analyte"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["analyte"]["properties"]["id"]["type"]

Specimen.schema()['properties']["identifier"]
case_mapping["destination"]["name"] = "Specimen.identifier"
case_mapping["destination"]["title"] = Specimen.schema()["properties"]["identifier"]["title"]
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["identifier"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["identifier"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ---------------------------------
name = case_schema['mappings'][3]['source']['name']
print(name)

case_mapping = case_schema['mappings'][3]
case_mapping["source"]["description"] = data_dict["case"]["case"]["properties"]["created_datetime"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["case"]["case"]["category"]
case_mapping["source"]["type"] = data_dict["case"]["case"]["properties"]["created_datetime"]["oneOf"][0]["type"]

# created_datetime -> Extension.valueDateTime
Specimen.schema()['properties']["identifier"]
case_mapping["destination"]["name"] = "ResearchSubject.Extension.valueDateTime"
case_mapping["destination"]["title"] = Extension.schema()["properties"]["valueDateTime"]["title"]
case_mapping["destination"]["description"] = Extension.schema()["properties"]["valueDateTime"]["description"]
case_mapping["destination"]["type"] = Extension.schema()["properties"]["valueDateTime"]["type"]
case_mapping["destination"]["module"] = "Extensibility"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ---------------------------------
name = case_schema['mappings'][4]['source']['name']
print(name)

# TODO: days_to_index ? data_dict["case"]["case"]["properties"]["index_date"] ?
# case_mapping = case_schema['mappings'][4]
# ---------------------------------
name = case_schema['mappings'][5]['source']['name']
print(name)

# portion_ids -> Specimen.identifier
case_mapping = case_schema['mappings'][5]
case_mapping["source"]["description"] = data_dict["biospecimen"]["portion"]["properties"]["id"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["portion"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["portion"]["properties"]["id"]["type"]

Specimen.schema()['properties']["identifier"]
case_mapping["destination"]["name"] = "Specimen.identifier"
case_mapping["destination"]["title"] = Specimen.schema()["properties"]["identifier"]["title"]
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["identifier"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["identifier"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ---------------------------------
name = case_schema['mappings'][7]['source']['name']
print(name)

# slide_ids -> ImagingStudy.identifier
case_mapping = case_schema['mappings'][7]
case_mapping["source"]["description"] = data_dict["biospecimen"]["slide"]["properties"]["id"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["slide"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["slide"]["properties"]["id"]["type"]


case_mapping["destination"]["name"] = "ImagingStudy.identifier"
case_mapping["destination"]["title"] = ImagingStudy.schema()["properties"]["identifier"]["title"]
case_mapping["destination"]["description"] = ImagingStudy.schema()["properties"]["identifier"]["description"]
case_mapping["destination"]["type"] = ImagingStudy.schema()["properties"]["identifier"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"
utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ---------------------------------
name = case_schema['mappings'][8]['source']['name']
print(name)

# state -> ResearchSubject.status
case_mapping = case_schema['mappings'][8]
case_mapping["source"]["description"] = data_dict["case"]["case"]["properties"]["state"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["case"]["case"]["category"]
case_mapping["source"]["type"] = "string"
case_mapping["source"]["content_annotation"] = data_dict["case"]["case"]["properties"]["state"]["oneOf"]


case_mapping["destination"]["name"] = "ResearchSubject.status" # TODO: does this need to be an extension - status values don't match
case_mapping["destination"]["title"] = ResearchSubject.schema()["properties"]["status"]["title"]
case_mapping["destination"]["description"] = ResearchSubject.schema()["properties"]["status"]["description"]
case_mapping["destination"]["type"] = ResearchSubject.schema()["properties"]["status"]["type"]
case_mapping["destination"]["module"] = "Administration"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ---------------------------------
name = case_schema['mappings'][9]['source']['name']
print(name)

# submitter_aliquot_ids -> Specimen.id
case_mapping = case_schema['mappings'][9]
case_mapping["source"]["description"] = data_dict["biospecimen"]["aliquot"]["properties"]["submitter_id"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["aliquot"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["aliquot"]["properties"]["submitter_id"]["type"]

case_mapping["destination"]["name"] = "Specimen.id"
case_mapping["destination"]["title"] = Specimen.schema()["properties"]["id"]["title"]
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][10]['source']['name']
print(name)

# submitter_analyte_ids -> Specimen.id
case_mapping = case_schema['mappings'][10]
case_mapping["source"]["description"] = data_dict["biospecimen"]["analyte"]["properties"]["submitter_id"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["analyte"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["analyte"]["properties"]["submitter_id"]["type"]


case_mapping["destination"]["name"] = "Specimen.id"
case_mapping["destination"]["title"] = Specimen.schema()["properties"]["id"]["title"]
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][11]['source']['name']
print(name)

# submitter_ids -> ResearchSubject.id
case_mapping = case_schema['mappings'][11]
case_mapping["source"]["description"] = data_dict["case"]["case"]["properties"]["submitter_id"]["description"]
case_mapping["source"]["category"] = data_dict["case"]["case"]["category"]
case_mapping["source"]["type"] = data_dict["case"]["case"]["properties"]["submitter_id"]["type"]


case_mapping["destination"]["name"] = "ResearchSubject.id"
case_mapping["destination"]["title"] = ResearchSubject.schema()["properties"]["id"]["title"]
case_mapping["destination"]["description"] = ResearchSubject.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = ResearchSubject.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Administration"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][12]['source']['name']
print(name)

# submitter_portion_ids -> Specimen.id
case_mapping = case_schema['mappings'][12]
case_mapping["source"]["description"] = data_dict["biospecimen"]["portion"]["properties"]["submitter_id"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["portion"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["portion"]["properties"]["submitter_id"]["type"]


case_mapping["destination"]["name"] = "Specimen.id"
case_mapping["destination"]["title"] = Specimen.schema()["properties"]["id"]["title"]
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][13]['source']['name']
print(name)

# submitter_sample_ids -> Specimen.id
case_mapping = case_schema['mappings'][13]
case_mapping["source"]["description"] = data_dict["biospecimen"]["sample"]["properties"]["submitter_id"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["sample"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["sample"]["properties"]["submitter_id"]["type"]


case_mapping["destination"]["name"] = "Specimen.id"
case_mapping["destination"]["title"] = Specimen.schema()["properties"]["id"]["title"]
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][14]['source']['name']
print(name)

# submitter_slide_ids -> ImagingStudy.id
case_mapping = case_schema['mappings'][14]
case_mapping["source"]["description"] = data_dict["biospecimen"]["slide"]["properties"]["submitter_id"]["description"]
case_mapping["source"]["category"] = data_dict["biospecimen"]["slide"]["category"]
case_mapping["source"]["type"] = data_dict["biospecimen"]["slide"]["properties"]["submitter_id"]["type"]


case_mapping["destination"]["name"] = "ImagingStudy.id"
case_mapping["destination"]["title"] = ImagingStudy.schema()["properties"]["id"]["title"]
case_mapping["destination"]["description"] = ImagingStudy.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = ImagingStudy.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][15]['source']['name']
print(name)

# updated_datetime -> Extension.valueDateTime
case_mapping = case_schema['mappings'][15]
case_mapping["source"]["description"] = data_dict["case"]["case"]["properties"]["updated_datetime"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["case"]["case"]["category"]
case_mapping["source"]["type"] = data_dict["case"]["case"]["properties"]["updated_datetime"]["oneOf"][0]["type"]


case_mapping["destination"]["name"] = "ResearchSubject.Extension.valueDateTime"
case_mapping["destination"]["title"] = Extension.schema()["properties"]["valueDateTime"]["title"]
case_mapping["destination"]["description"] = Extension.schema()["properties"]["valueDateTime"]["description"]
case_mapping["destination"]["type"] = Extension.schema()["properties"]["valueDateTime"]["type"]
case_mapping["destination"]["module"] = "Extensibility"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])

# ------------------------------
name = case_schema['mappings'][16]['source']['name']
print(name)

# annotations.annotation_id -> Annotation.id
case_mapping = case_schema['mappings'][16]
case_mapping["source"]["description"] = data_dict["annotations"]["annotation"]["properties"]["id"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["annotations"]["annotation"]["category"]
case_mapping["source"]["type"] = data_dict["annotations"]["annotation"]["properties"]["id"]["type"]


# TODO: ResearchSubject not listed as "used in following places" https://build.fhir.org/datatypes.html#annotation
case_mapping["destination"]["name"] = "ResearchSubject.Annotation.id"  # identifier - not listed for annotations
case_mapping["destination"]["title"] = Annotation.schema()["properties"]["id"]["title"]
case_mapping["destination"]["description"] = Annotation.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = Annotation.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Foundation"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------ # TODO: best FHIR obj for GDC annotations ?
name = case_schema['mappings'][17]['source']['name']
print(name)

case_mapping = case_schema['mappings'][17]

# ------------------------------
name = case_schema['mappings'][18]['source']['name']
print(name)

case_mapping = case_schema['mappings'][18]
# ------------------------------
name = case_schema['mappings'][19]['source']['name']
print(name)

case_mapping = case_schema['mappings'][19]
# ------------------------------
name = case_schema['mappings'][20]['source']['name']
print(name)

case_mapping = case_schema['mappings'][20]
# ------------------------------
name = case_schema['mappings'][21]['source']['name']
print(name)

case_mapping = case_schema['mappings'][21]
# ------------------------------
name = case_schema['mappings'][22]['source']['name']
print(name)

case_mapping = case_schema['mappings'][22]
# ------------------------------
name = case_schema['mappings'][23]['source']['name']
print(name)

case_mapping = case_schema['mappings'][23]
# ------------------------------
name = case_schema['mappings'][24]['source']['name']
print(name)

case_mapping = case_schema['mappings'][24]
# ------------------------------
name = case_schema['mappings'][25]['source']['name']
print(name)

case_mapping = case_schema['mappings'][25]
# ------------------------------
name = case_schema['mappings'][26]['source']['name']
print(name)

case_mapping = case_schema['mappings'][26]
# ------------------------------
name = case_schema['mappings'][27]['source']['name']
print(name)

case_mapping = case_schema['mappings'][27]
# ------------------------------
name = case_schema['mappings'][28]['source']['name']
print(name)

case_mapping = case_schema['mappings'][28]
# ------------------------------
name = case_schema['mappings'][29]['source']['name']
print(name)

case_mapping = case_schema['mappings'][29]
# ------------------------------
name = case_schema['mappings'][30]['source']['name']
print(name)

case_mapping = case_schema['mappings'][30]
# ------------------------------
name = case_schema['mappings'][31]['source']['name']
print(name)

case_mapping = case_schema['mappings'][31]
# ------------------------------
name = case_schema['mappings'][32]['source']['name']
print(name)

case_mapping = case_schema['mappings'][32]
# ------------------------------
name = case_schema['mappings'][33]['source']['name']
print(name)

# demographic.created_datetime -> Patient.Extension.valueDateTime
case_mapping = case_schema['mappings'][33]
case_mapping["source"]["description"] = data_dict["clinical"]["demographic"]["properties"]["created_datetime"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["demographic"]["category"]
case_mapping["source"]["type"] = data_dict["clinical"]["demographic"]["properties"]["created_datetime"]["oneOf"][0]["type"]


case_mapping["destination"]["name"] = "Patient.Extension.valueDateTime"
case_mapping["destination"]["title"] = Extension.schema()["properties"]["valueDateTime"]["title"]
case_mapping["destination"]["description"] = Extension.schema()["properties"]["valueDateTime"]["description"]
case_mapping["destination"]["type"] = Extension.schema()["properties"]["valueDateTime"]["type"]
case_mapping["destination"]["module"] = "Extensibility"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][34]['source']['name']
print(name)

# demographic.demographic_id -> Patient.identifier
case_mapping = case_schema['mappings'][34]
case_mapping["source"]["description"] = data_dict["clinical"]["demographic"]["properties"]["id"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["demographic"]["category"]
case_mapping["source"]["type"] = "string"


case_mapping["destination"]["name"] = "Patient.identifier"
case_mapping["destination"]["title"] = Patient.schema()["properties"]['identifier']["title"]
case_mapping["destination"]["description"] = Patient.schema()["properties"]['identifier']["title"]
case_mapping["destination"]["type"] = Patient.schema()["properties"]['identifier']["type"]
case_mapping["destination"]["module"] = "Administration"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][36]['source']['name']
print(name)

# demographic.gender -> Patient.gender
case_mapping = case_schema['mappings'][36]
case_mapping["source"]["description"] = data_dict["clinical"]["demographic"]["properties"]["gender"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["demographic"]["category"]
case_mapping["source"]["type"] = data_dict["case"]["case"]["properties"]["id"]["type"]
case_mapping["source"]["content_annotation"] = "@./resources/gdc_resources/content_annotations/demographic/gender.json"

case_mapping["destination"]["name"] = "Patient.gender"
case_mapping["destination"]["title"] = Patient.schema()["properties"]["gender"]["title"]
case_mapping["destination"]["description"] = Patient.schema()["properties"]["gender"]["description"]
case_mapping["destination"]["type"] = Patient.schema()["properties"]["gender"]["type"]
case_mapping["destination"]["module"] = "Administration"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][38]['source']['name']
print(name)

# TODO: demographic.state -> Patient.X ?
case_mapping = case_schema['mappings'][38]
# ------------------------------
name = case_schema['mappings'][39]['source']['name']
print(name)

# demographic.submitter_id -> Patient.id
case_mapping = case_schema['mappings'][39]
case_mapping["source"]["description"] = data_dict["clinical"]["demographic"]["properties"]["submitter_id"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["demographic"]["category"]
case_mapping["source"]["type"] = data_dict["clinical"]["demographic"]["properties"]["submitter_id"]["type"]


case_mapping["destination"]["name"] = "Patient.id"
case_mapping["destination"]["title"] = Patient.schema()["properties"]["id"]["title"]
case_mapping["destination"]["description"] = Patient.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = Patient.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Administration"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][40]['source']['name']
print(name)

# demographic.updated_datetime -> Patient.Extension.valueDateTime
case_schema['mappings'][40]['source']['name'] = "demographic.updated_datetime"
case_mapping["source"]["description"] = data_dict["clinical"]["demographic"]["properties"]["updated_datetime"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["demographic"]["category"]
case_mapping["source"]["type"] = data_dict["clinical"]["demographic"]["properties"]["updated_datetime"]["oneOf"][0]["type"]

case_mapping["destination"]["name"] = "Patient.Extension.valueDateTime"
case_mapping["destination"]["title"] = Extension.schema()["properties"]["valueDateTime"]["title"]
case_mapping["destination"]["description"] = Extension.schema()["properties"]["valueDateTime"]["description"]
case_mapping["destination"]["type"] = Extension.schema()["properties"]["valueDateTime"]["type"]
case_mapping["destination"]["module"] = "Extensibility"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][42]['source']['name']
print(name)

# demographic.year_of_death -> Patient.deceasedDateTime
case_mapping = case_schema['mappings'][42]
case_mapping["source"]["description"] = data_dict["clinical"]["demographic"]["properties"]["year_of_death"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["demographic"]["category"]
case_mapping["source"]["type"] = data_dict["clinical"]["demographic"]["properties"]["year_of_death"]["type"]


case_mapping["destination"]["name"] = "Patient.deceasedDateTime"
case_mapping["destination"]["title"] = Patient.schema()["properties"]["deceasedDateTime"]["title"]
case_mapping["destination"]["description"] = Patient.schema()["properties"]["deceasedDateTime"]["title"]
case_mapping["destination"]["type"] = Patient.schema()["properties"]["deceasedDateTime"]["type"]
case_mapping["destination"]["module"] = "Administration"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][43]['source']['name']
print(name)

# diagnoses.age_at_diagnosis -> Condition.onsetAge
case_mapping = case_schema['mappings'][43]
case_mapping["source"]["description"] = data_dict["clinical"]["diagnosis"]["properties"]["age_at_diagnosis"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["diagnosis"]["category"]
case_mapping["source"]["type"] = data_dict["clinical"]["diagnosis"]["properties"]["age_at_diagnosis"]["oneOf"][0]["type"]


case_mapping["destination"]["name"] = "Condition.onsetAge"
case_mapping["destination"]["title"] = Condition.schema()["properties"]["onsetAge"]["title"]
case_mapping["destination"]["description"] = Condition.schema()["properties"]["onsetAge"]["description"]
case_mapping["destination"]["type"] = Condition.schema()["properties"]["onsetAge"]["type"]
case_mapping["destination"]["module"] = "Clinical_Summary"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][44]['source']['name']
print(name)

# diagnoses.classification_of_tumor -> Condition.category
case_mapping = case_schema['mappings'][44]
case_mapping["source"]["description"] = data_dict["clinical"]["diagnosis"]["properties"]["classification_of_tumor"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["diagnosis"]["category"]
case_mapping["source"]["type"] = "string"
# TODO: there are cases with multiple enums - standardizing it would be something like below
# case_mapping["source"]["enums"] = [{"enum": data_dict["clinical"]["diagnosis"]["properties"]["classification_of_tumor"]["enum"]}]
case_mapping["source"]["enum"] = data_dict["clinical"]["diagnosis"]["properties"]["classification_of_tumor"]["enum"]
case_mapping["source"]["content_annotation"] = "@./resources/gdc_resources/content_annotations/diagnosis/classification_of_tumor.json"

case_mapping["destination"]["name"] = "Condition.category"
case_mapping["destination"]["title"] = Condition.schema()["properties"]["category"]["title"]
case_mapping["destination"]["description"] = Condition.schema()["properties"]["category"]["description"]
case_mapping["destination"]["type"] = Condition.schema()["properties"]["category"]["type"]
case_mapping["destination"]["module"] = "Clinical_Summary"

utils.initialize_content_annotations(data_dict["clinical"]["diagnosis"]["properties"]["classification_of_tumor"]["enumDef"], "./resources/gdc_resources/content_annotations/diagnosis/classification_of_tumor.json")
utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------
name = case_schema['mappings'][45]['source']['name']
print(name)

# diagnoses.created_datetime -> Condition.onsetDateTime
case_mapping = case_schema['mappings'][45]
case_mapping["source"]["description"] = data_dict["clinical"]["diagnosis"]["properties"]["created_datetime"]["common"]["description"]
case_mapping["source"]["category"] = data_dict["clinical"]["diagnosis"]["category"]
case_mapping["source"]["type"] = data_dict["clinical"]["diagnosis"]["properties"]["created_datetime"]["oneOf"][0]["type"]

case_mapping["destination"]["name"] = "Condition.onsetDateTime"
case_mapping["destination"]["title"] = Condition.schema()["properties"]["onsetDateTime"]["title"]
case_mapping["destination"]["description"] = Condition.schema()["properties"]["onsetDateTime"]["description"]
case_mapping["destination"]["type"] = Condition.schema()["properties"]["onsetDateTime"]["type"]
case_mapping["destination"]["module"] = "Clinical_Summary"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------ Brainstorming
# case
Coding.schema()['properties']['code']['description']
Patient.schema()['properties']
Observation.schema()['properties']
ObservationDefinition.schema()['properties']
Extension.schema()['properties']
ResearchStudy.schema()['properties']
GenomicStudyAnalysis.schema()['properties']['changeType']
ResearchSubject.schema()['properties']
Specimen.schema()['properties']['identifier']

# file
DocumentReference.schema()['properties']
Attachment.schema()['properties']['title']['title']
Attachment.schema()['properties']['size']['title']
Extension.schema()['properties']['valueString']


names_to_map = []
for mapping in case_schema['mappings']:
    if not mapping['destination']['name']:
        names_to_map.append(mapping['source']['name'])
# len(names_to_map)
# 776

with open("./mapping/case.json", 'w', encoding='utf-8') as file:
    json.dump(case_schema, file, indent=4)



