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

from fhir.resources.documentreference import DocumentReference
from fhir.resources.attachment import Attachment

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


# read in schema and update relations
case_schema_path = "./mapping/case.json"
if os.path.isfile(case_schema_path):
    case_schema = utils.read_schema(case_schema_path)

case_schema['mappings'][0]['source']['name']

names_to_map = []
for mapping in case_schema['mappings']:
    if not mapping['destination']['name']:
        names_to_map.append(mapping['source']['name'])
# len(names_to_map)
# 776

# update_values(case_schema, source_name, source=True, destination=False, source_values=None, destination_values=None)
"""
with open("./mapping/resources/gdc_resources/case_test.json", 'w', encoding='utf-8') as file:
    json.dump(case_schema, file, indent=4)
"""

