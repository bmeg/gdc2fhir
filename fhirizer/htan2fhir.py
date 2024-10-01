import uuid
import json
import orjson
import copy
import glob
import pathlib
import inflection
import itertools
import pandas as pd
from fhirizer import utils
from pathlib import Path
import importlib.resources
from uuid import uuid3, NAMESPACE_DNS

from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.patient import Patient
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.researchsubject import ResearchSubject
from fhir.resources.specimen import Specimen, SpecimenProcessing, SpecimenCollection
from fhir.resources.condition import Condition, ConditionStage
from fhir.resources.documentreference import DocumentReference, DocumentReferenceContent, \
    DocumentReferenceContentProfile
from fhir.resources.attachment import Attachment
from fhir.resources.observation import Observation
from fhir.resources.medicationadministration import MedicationAdministration
from fhir.resources.medication import Medication

# File data on synapse after authentication
# https://github.com/Sage-Bionetworks/synapsePythonClient?tab=readme-ov-file#store-a-file-to-synapse

project_id = "OHSU_Breast_NOS"
project_path = "./projects/HTAN/OHSU/Breast_NOS"

SYSTEM_HTAN = 'https://data.humantumoratlas.org'
NAMESPACE_HTAN = uuid3(NAMESPACE_DNS, SYSTEM_HTAN)
verbose = True

cases_mapping = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'htan_resources' / 'cases.json')))

biospecimens_mapping = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'htan_resources' / 'biospecimens.json')))

files_mapping = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'htan_resources' / 'files.json')))

# https://jen-dfci.github.io/htan_missing_manual/data_model/overview/

# cases_mappings
# https://data.humantumoratlas.org/standard/clinical
# cases to Patient / ResearchSubject / ResearchStudy / Observation -> Condition / Medication / MedicationAdministration / Procedure / Encounter
# 'HTAN Participant ID':  #NOTE:  HTAN ID associated with a patient based on HTAN ID SOP
# 'Therapeutic Agents':  #NOTE: Some have multiple comma-separated Medication.ingredient
cases_path = "".join([project_path, "/raw/cases/table_data.tsv"])
cases = pd.read_csv(cases_path, sep="\t")

# identifiers of the cases matrix/df
patient_identifier_field = "HTAN Participant ID"


def get_htan_field(match, field_maps, map_info):
    for field, mappings in field_maps.items():
        assert isinstance(mappings, list), f"HTAN resource mappings is not a list: {type(mappings)}, {mappings}"
        for entry_map in mappings:
            if entry_map[map_info] and entry_map[map_info] == match:
                yield field
                break


components_fields = []
for key in get_htan_field(match='Condition', field_maps=cases_mapping, map_info='focus'):
    components_fields.append(key)
    if verbose:
        print(f"Observation focus -> condition - filed': {key}")

observation_component_df = cases[[patient_identifier_field] + components_fields]


for key in get_htan_field(match='Observation.component', field_maps=cases_mapping, map_info='fhir_map'):
    if verbose:
        print(f"field name mapped to Observation.component': {key}")

# _component = utils.get_component(key=field, value=_component_value, component_type=utils.get_data_types(type(_component_value)), system=SYSTEM_HTAN)

# format for onsetAge
# "onsetAge": {
#     "value": 23194,
#     "unit": "days",
#     "system": "http://unitsofmeasure.org",
#     "code": "d"
# }

# biospecimens_mapping
# biospecimens to Specimen / Observation -> Specimen
# 'HTAN Parent ID': #NOTE: Parent could be another biospecimen or a research participant. # check for participant id for type of reference
# 'Biospecimen Type': #NOTE: Doesn't seem informative
biospecimens_path = "".join([project_path, "/raw/biospecimens/table_data.tsv"])
biospecimens = pd.read_csv(biospecimens_path, sep="\t")
biospecimen_identifier_field = "HTAN Biospecimen ID"

# files_mapping
# files to DocumentReference / Attachment / Observation -> DocumentReference
files_metadata = pd.read_csv("".join([project_path, "/raw/files/table_data.tsv"]), sep="\t")
files_drs_uri = pd.read_csv("".join([project_path, "/raw/files/cds_manifest.csv"]))
