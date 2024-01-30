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
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["identifier"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["identifier"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ---------------------------------
name = case_schema['mappings'][3]['source']['name']
print(name)

case_mapping = case_schema['mappings'][3]
case_mapping["source"]["description"] = data_dict["case"]["case"]["properties"]["created_datetime"]["common"]["description"]
case_mapping["source"]["category"] = "case"
case_mapping["source"]["type"] = data_dict["case"]["case"]["properties"]["created_datetime"]["oneOf"][0]["type"]

# created_datetime -> Extention.valueDateTime
Specimen.schema()['properties']["identifier"]
case_mapping["destination"]["name"] = "Observation.Extention.valueDateTime"
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
case_mapping["source"]["category"] = "case"
case_mapping["source"]["type"] = "string"
case_mapping["source"]["content_annotation"] = data_dict["case"]["case"]["properties"]["state"]["oneOf"]


case_mapping["destination"]["name"] = "ResearchSubject.status"
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
case_mapping["destination"]["description"] = Specimen.schema()["properties"]["id"]["description"]
case_mapping["destination"]["type"] = Specimen.schema()["properties"]["id"]["type"]
case_mapping["destination"]["module"] = "Diagnostics"

utils.update_values(case_schema, source_name=name, source=True, destination=True, source_values=case_mapping["source"], destination_values=case_mapping["destination"])
# ------------------------------


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



