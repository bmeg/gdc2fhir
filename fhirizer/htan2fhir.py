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
from typing import Any

from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.patient import Patient
from fhir.resources.address import Address
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


class HTANTransformer:
    def __init__(self, subprogram_name: str, project_id: str, verbose: bool):
        self.mint_id = utils.mint_id
        self._mint_id = utils._mint_id
        self.get_data_type = utils.get_data_types
        self.get_component = utils.get_component
        self.fhir_ndjson = utils.fhir_ndjson
        self.subprogram_name = subprogram_name
        self.project_id = project_id
        self.verbose = verbose
        self.SYSTEM_HTAN = 'https://data.humantumoratlas.org'
        self.NAMESPACE_HTAN = uuid3(NAMESPACE_DNS, self.SYSTEM_HTAN)
        self.project_id = project_id
        self.read_json = utils._read_json

        self.project_path = str(
            Path(importlib.resources.files('fhirizer').parent / 'projects' / 'HTAN' / subprogram_name / project_id))
        assert Path(self.project_path).is_dir(), f"Path {self.project_path} is not a valid directory path."

        self.cases_path = str(
            Path(importlib.resources.files('fhirizer').parent / 'resources' / 'htan_resources' / 'cases.json'))
        assert Path(self.cases_path).is_file(), f"Path {self.cases_path} does not exist."

        self.biospecimens_path = str(
            Path(importlib.resources.files('fhirizer').parent / 'resources' / 'htan_resources' / 'biospecimens.json'))
        assert Path(self.biospecimens_path).is_file(), f"Path {self.biospecimens_path} does not exist."

        self.files_path = str(
            Path(importlib.resources.files('fhirizer').parent / 'resources' / 'htan_resources' / 'files.json'))
        assert Path(self.files_path).is_file(), f"Path {self.files_path} does not exist."

        self.cases_mappings = self.get_cases_mappings

        # cases_mappings
        # https://data.humantumoratlas.org/standard/clinical
        # cases to Patient / ResearchSubject / ResearchStudy / Observation -> Condition / Medication / MedicationAdministration / Procedure / Encounter
        # 'HTAN Participant ID':  #NOTE:  HTAN ID associated with a patient based on HTAN ID SOP
        # 'Therapeutic Agents':  #NOTE: Some have multiple comma-separated Medication.ingredient
        self.cases_table_data_path = Path(Path(self.project_path).parent / self.project_id).joinpath("./raw/cases/table_data.tsv")
        assert self.cases_table_data_path.is_file(), f"Path {self.cases_table_data_path} is not a valid file path."
        self.cases = self.get_dataframe(self.cases_table_data_path, sep="\t")
        self.patient_identifier_field = "HTAN Participant ID" # identifiers of the cases matrix/df

        self.biospecimen_mappings = self.get_biospecimen_mappings

        # biospecimens_mapping
        # biospecimens to Specimen / Observation -> Specimen
        # 'HTAN Parent ID': #NOTE: Parent could be another biospecimen or a research participant. # check for participant id for type of reference
        # 'Biospecimen Type': #NOTE: Doesn't seem informative
        self.biospecimens_table_data_path = Path(Path(self.project_path).parent / self.project_id).joinpath(
            "./raw/biospecimens/table_data.tsv")
        assert self.biospecimens_table_data_path.is_file(), f"Path {self.biospecimens_table_data_path} is not a valid file path."
        self.biospecimens = self.get_dataframe(self.biospecimens_table_data_path, sep="\t")
        self.biospecimen_identifier_field = "HTAN Biospecimen ID"

        self.files_mappings = self.get_files_mappings

        # files_mapping
        # files to DocumentReference / Attachment / Observation -> DocumentReference

        self.files_table_data_path = Path(Path(self.project_path).parent / self.project_id).joinpath("./raw/files/table_data.tsv")
        self.files_drs_uri_path = Path(Path(self.project_path).parent / self.project_id).joinpath("./raw/files/cds_manifest.csv")
        assert self.files_table_data_path.is_file(), f"Path {self.files_table_data_path} is not a valid file path."
        assert self.files_drs_uri_path.is_file(), f"Path {self.files_drs_uri_path} is not a valid file path."

        self.files = self.get_dataframe(self.files_table_data_path, sep="\t")
        self.files_drs_uri = pd.read_csv(self.files_drs_uri_path, sep=",")

        self.patient_demographics = self.get_patient_demographics()

    def get_cases_mappings(self) -> dict:
        """HTAN cases FHIR mapping"""
        return self.read_json(self.cases_path)

    def get_biospecimen_mappings(self) -> dict:
        """HTAN biospesimens FHIR mapping"""
        return self.read_json(self.biospecimens_path)

    def get_files_mappings(self) -> dict:
        """HTAN files FHIR mapping"""
        return self.read_json(self.files_path)

    @staticmethod
    def get_dataframe(_path, sep) -> pd.DataFrame:
        """Returns a Pandas DataFrame with lower-case and inflection.underscore columns for standard UI input"""
        _data = pd.read_csv(_path, sep=sep)
        # _data.columns = _data.columns.to_series().apply(lambda x: inflection.underscore(inflection.parameterize(x)))
        return _data

    def get_patient_demographics(self) -> pd.DataFrame:
        """HTAN cases table_data.tsv data with Patient FHIR demographics mappings column/field match"""
        field_list = []
        for field in self.get_htan_mapping(match='Patient', field_maps=self.cases_mappings(), map_info='fhir_map', fetch='field'):
            field_list.append(field)
            if self.verbose:
                print(f"field name': {field}")

        patient_demographics = self.cases[field_list]
        return patient_demographics

    @staticmethod
    def get_htan_mapping(match, field_maps, map_info, fetch):
        """Yields FHIR HTAN maps from HTAN field or FHIR mapping string"""
        for field, mappings in field_maps.items():
            assert isinstance(mappings, list), f"HTAN resource mappings is not a list: {type(mappings)}, {mappings}"
            for entry_map in mappings:
                if entry_map[map_info] and match in entry_map[map_info]:
                    if fetch == "field":
                        yield field
                        break
                    elif fetch == "mapping":
                        yield entry_map
                        break

    @staticmethod
    def get_fields_by_fhir_map(mapping_data, fhir_mapping=None):
        """
        Yields the field(s) associated with a specific HTAN FHIR map or all HTAN FHIR maps

        Return: Yields the field, FHIR map, identifier use, and focus.
            example:
                for field, fhir_map, use, focus in get_fields_by_fhir_map(cases_mapping, "Observation.component"):
                    print(f"Field: {field}, FHIR Map: {fhir_map}, Identifier use: {use}, Focus: {focus}")
        """
        for _field, mappings in mapping_data.items():
            for mapping in mappings:
                _current_fhir_map = mapping["fhir_map"]
                _focus = mapping.get("focus", None)
                _use = mapping.get("use", None)

                if fhir_mapping is None or _current_fhir_map == fhir_mapping:
                    yield _field, _current_fhir_map, _use, _focus

    @staticmethod
    def get_fhir_maps_by_field(mapping_data, field_name=None):
        """
        Yields the FHIR map(s) associated with a specific HTAN field or all HTAN FHIR maps

        Return: Yields the field, FHIR map, identifier use, and focus.
            example use:
                for field, fhir_map, use, focus in get_fhir_maps_by_field(cases_mapping, "Year of Diagnosis"):
                    print(f"Field: {field}, FHIR Map: {fhir_map}, Identifier use: {use}, Focus: {focus}")
        """
        for _field, mappings in mapping_data.items():
            if field_name is None or _field == field_name:
                for mapping in mappings:
                    _fhir_map = mapping["fhir_map"]
                    _focus = mapping.get("focus", None)
                    _use = mapping.get("use", None)
                    yield _field, _fhir_map, _use, _focus


class PatientTransformer(HTANTransformer):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(**kwargs)
        self.cases_mapping = self.cases_mappings
        self.NAMESPACE_HTAN = self.NAMESPACE_HTAN
        self.get_data_types = utils.get_data_types
        self.get_component = self.get_component
        self.get_fields_by_fhir_map = self.get_fields_by_fhir_map

    def create_patient(self, _row: pd.Series) -> Patient:
        """Transform HTAN case demographics to FHIR Patient"""
        use = None
        for _field, _fhir_map, _use, _focus in self.get_fields_by_fhir_map(self.cases_mapping(), "Patient.identifier"):
            use = _use
        assert use, f"Patient.identifier use is not defined in ./resources/HTAN/cases.json mappings."

        patient_identifier = Identifier(**{"system": self.SYSTEM_HTAN, "value": _row['HTAN Participant ID'], "use": use})
        patient_id = self.mint_id(identifier=patient_identifier, resource_type="Patient", project_id=self.project_id,
                                   namespace=self.NAMESPACE_HTAN)

        deceasedBoolean_fields = []
        for _field, _fhir_map, _use, _focus in self.get_fields_by_fhir_map(self.cases_mapping(), "Patient.deceasedBoolean"):
            deceasedBoolean_fields.append(_field)
        assert deceasedBoolean_fields, f"Patient.deceasedBoolean has no fields defined in ./resources/HTAN/cases.json mappings."


        vital_status = _row[deceasedBoolean_fields].dropna().unique().any()
        deceasedBoolean = {"Dead": True}.get(vital_status, False if vital_status else None)

        # TODO: us-core-ethnicity and race resource
        ethnicity = _row.get("Ethnicity")
        race = _row.get("Race")

        address_country = _row.get("Country of Residence")
        address = Address(**{"country": address_country})

        return Patient(**{"id": patient_id,
                          "identifier": [patient_identifier],
                          "deceasedBoolean": deceasedBoolean,
                          "extension": [{"url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                                         "valueString": ethnicity},
                                        {"url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                                         "valueString": race}
                                        ],
                          "address": [address]})

    def patient_observation(self, patient: Patient, _row: pd.Series) -> Observation:
        patient_observation_fields = []
        for field, fhir_map, use, focus in self.get_fields_by_fhir_map(transformer.cases_mappings(), "Observation.component"):
            if focus == "Patient":
                patient_observation_fields.append(field)

        if patient_observation_fields:
            _obervation_row = _row[patient_observation_fields]

        components = []
        for key, value in _obervation_row.to_dict().items():
            if key != 'HTAN Participant ID':
                if isinstance(value, float) and not pd.isna(value) and ("Year" in key or "Day" in key or "year" in key or "day" in key):
                    value = int(value)
                    _component = self.get_component(key=key, value=value, component_type=self.get_data_types(type(value).__name__), system=self.SYSTEM_HTAN)
                    components.append(_component)

        observation_identifier = Identifier(**{"system": self.SYSTEM_HTAN, "use": "official", "value": patient.id})
        observation_id = self.mint_id(identifier=observation_identifier, resource_type="Observation",
                                      project_id=self.project_id, namespace=self.NAMESPACE_HTAN)

        return Observation(**{"id": observation_id,
                              "identifier": [observation_identifier],
                              "status": "final",
                              "category": [
                                  {
                                      "coding": [
                                          {
                                              "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                              "code": "exam",
                                              "display": "exam"
                                          }
                                      ],
                                      "text": "Exam"
                                  }
                              ],
                              "code": {
                                  "coding": [
                                      {
                                          "system": "http://loinc.org",
                                          "code": "52460-3", # TODO: may need to change to be more specific
                                          "display": "patient information"
                                      }
                                  ],
                                  "text": "Patient Information"
                              },
                              "focus": [Reference(**{"reference": f"Patient/{patient.id}"})],
                              "subject": Reference(**{"reference": f"Patient/{patient.id}"}),
                              "component": components})


transformer = HTANTransformer(subprogram_name="OHSU", project_id="Breast_NOS", verbose=False)
patient_transformer = PatientTransformer(subprogram_name="OHSU", project_id="Breast_NOS", verbose=False)
patient_demographics_df = transformer.patient_demographics
cases = transformer.cases

patients = []
for index, row in cases.iterrows():
    patient_row = cases.iloc[index][patient_demographics_df.columns]
    patient = patient_transformer.create_patient(_row=patient_row)
    patient_obs = patient_transformer.patient_observation(patient=patient, _row=row)
    if patient:
        patients.append(orjson.loads(patient.json()))
        print(f"HTAN FHIR Patient: {patient.json()}")
        print(f"HTAN FHIR Patient Observation: {patient_obs.json()}")
