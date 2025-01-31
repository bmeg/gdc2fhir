import os
import re
import uuid
import json
import copy
import orjson
from iteration_utilities import unique_everseen  # unresolved in pycharm - ok in pip freeze and ipython import
from fhir.resources.identifier import Identifier
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.researchstudy import ResearchStudyRecruitment
from fhir.resources.extension import Extension
from fhir.resources.reference import Reference
from fhir.resources.group import Group, GroupMember
from fhir.resources.condition import Condition, ConditionStage
from fhir.resources.observation import Observation, ObservationComponent
from fhir.resources.practitioner import Practitioner
from fhir.resources.organization import Organization
from fhir.resources.specimen import Specimen, SpecimenProcessing, SpecimenCollection
from fhir.resources.patient import Patient
from fhir.resources.researchsubject import ResearchSubject
from fhir.resources.imagingstudy import ImagingStudy, ImagingStudySeries
from fhir.resources.medicationadministration import MedicationAdministration
from fhir.resources.bodystructure import BodyStructure, BodyStructureIncludedStructure
from fhir.resources.medication import Medication
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.documentreference import DocumentReference, DocumentReferenceContent, \
    DocumentReferenceContentProfile
from fhir.resources.attachment import Attachment
from fhir.resources.age import Age
from fhirizer import utils, mapping
from datetime import datetime
import icd10
import importlib.resources
from pathlib import Path
from uuid import uuid3, NAMESPACE_DNS

disease_types = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'case' / 'disease_types.json')))
primary_sites = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'case' / 'primary_sites.json')))
race = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'demographic' / 'race.json')))
ethnicity = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'demographic' / 'ethnicity.json')))
gender = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'demographic' / 'gender.json')))
data_dict = utils.load_data_dictionary(path=utils.DATA_DICT_PATH)
cancer_pathological_staging = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'diagnosis' / 'cancer_pathological_staging.json')))
ncit2mondo = utils.ncit2mondo(
    str(Path(importlib.resources.files('fhirizer').parent / 'resources' / 'ncit2mondo.json.gz')))
biospecimen_observation = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'biospecimen' / 'biospecimen_observation.json')))
biospecimen_imaging_observation = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'biospecimen' / 'biospecimen_imaging_observation.json')))
social_histody_smoking_observation = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'case' / 'social_history_smoking_observations.json')))
social_histody_alcohol_observation = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'case' / 'social_history_alcohol_observations.json')))
aliquot = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'biospecimen' / 'aliquot.json')))
file_observation = utils._read_json(
    str(Path(importlib.resources.files('fhirizer').parent / 'resources' / 'gdc_resources'
             / 'content_annotations' / 'files' / 'output_file_observation.json')))
diagnosis_survey = utils._read_json(str(Path(importlib.resources.files(
    'fhirizer').parent / 'resources' / 'gdc_resources' / 'content_annotations' / 'case' / 'diagnosis_survey.json')))


def create_researchstudy(project_data) -> tuple[ResearchStudy | None]:
    """Creates FHIR ResearchStudy"""
    project_id = "GDC"
    NAMESPACE_GDC = uuid3(NAMESPACE_DNS, 'gdc.cancer.gov')
    _rs_parent = None
    status = "active"
    value = project_data['ResearchStudy.id']
    assert value, "Can't create a ResearchStudy. GDC project id is missing."

    research_study_identifiers = []
    rs_identifier = Identifier(value=value, system="/".join(["https://gdc.cancer.gov", "project"]), use="official")
    rs_id = utils.mint_id(identifier=rs_identifier, resource_type="ResearchStudy", project_id=project_id,
                          namespace=NAMESPACE_GDC)
    research_study_identifiers.append(rs_identifier)

    if 'ResearchStudy.dbgap_accession_number' in project_data.keys() and project_data[
        'ResearchStudy.dbgap_accession_number']:
        rs_dbgap_identifier = Identifier(value=project_data['ResearchStudy.dbgap_accession_number'],
                                         system="/".join(["https://gdc.cancer.gov", "dbgap_accession_number"]),
                                         use='secondary')
        research_study_identifiers.append(rs_dbgap_identifier)

    name = None
    if 'ResearchStudy.name' in project_data.keys() and project_data['ResearchStudy.name']:
        name = project_data['ResearchStudy.name']

    condition = []
    if 'ResearchStudy.condition' in project_data.keys() and project_data['ResearchStudy.condition']:
        for c in project_data['ResearchStudy.condition']:
            for d in disease_types:
                if c in d['value']:
                    if d['sctid']:
                        code = None
                        if not isinstance(d['sctid'], str):
                            code = str(d['sctid'])
                            display = str(d['value'])
                        else:
                            code = d['sctid']
                            display = d['value']

                        condition_code = CodeableConcept(**{"coding": [{'system': 'http://snomed.info/sct',
                                                                        'display': display,
                                                                        'code': code}]})
                        if condition_code:
                            condition.append(condition_code)

    parent_reference = []
    if 'ResearchStudy' in project_data.keys() and project_data['ResearchStudy']:
        _rs_parent, _ = create_researchstudy(project_data=project_data['ResearchStudy'])
        parent_reference = [Reference(**{"reference": f"ResearchStudy/{_rs_parent.id}"})]

    rs = ResearchStudy(**{"id": rs_id,
                          "identifier": research_study_identifiers,
                          "status": status,
                          "name": name,
                          "title": name,
                          "partOf": parent_reference,
                          "condition": condition})

    return rs, _rs_parent  # only two hierarchy in GDC


# projects_path="./tests/fixtures/project/project_key.ndjson"


def create_imaging_study(slide, patient, sample):
    project_id = "GDC"
    NAMESPACE_GDC = uuid3(NAMESPACE_DNS, 'gdc.cancer.gov')

    img = ImagingStudy.model_construct()
    img.status = "available"
    img_identifiers = []

    img_identifier = Identifier(
        **{"system": "".join(["https://gdc.cancer.gov/", "slide_id"]),
           "value": slide["ImagingStudy.id"],
           "use": "official"})
    img_identifiers.append(img_identifier)
    img.id = utils.mint_id(identifier=img_identifier, resource_type="ImagingStudy",
                           project_id=project_id,
                           namespace=NAMESPACE_GDC)

    if "ImagingStudy.identifier" in slide.keys() and slide["ImagingStudy.identifier"]:
        slide_submitter_id = Identifier(
            **{"system": "".join(["https://gdc.cancer.gov/", "slide_id"]),
               "value": slide["ImagingStudy.identifier"],
               "use": "secondary"})
        img_identifiers.append(slide_submitter_id)

    img.identifier = img_identifiers
    img.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})

    img_series = ImagingStudySeries.model_construct()
    img_series.uid = sample.id

    # https://hl7.org/fhir/R4/codesystem-dicom-dcim.html#dicom-dcim-SM
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_D.html
    modality = CodeableConcept.model_construct()
    modality.coding = [
        {"system": " http://dicom.nema.org/resources/ontology/DCM", "display": "Slide Microscopy", "code": "SM"}]
    img_series.modality = modality

    img_series.specimen = [Reference(**{"reference": "/".join(["Specimen", sample.id])})]
    img.series = [img_series]

    return img


def specimen_exists(specimen_id, specimen_list):
    return any(specimen.id == specimen_id for specimen in specimen_list)


def add_specimen(dat, name, id_key, has_parent, parent, patient, all_fhir_specimens):
    if name in dat.keys():
        for sample in dat[name]:
            if id_key in sample.keys():
                fhir_specimen = Specimen.model_construct()
                fhir_specimen.id = sample[id_key]
                fhir_specimen.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})
                if has_parent:
                    fhir_specimen.parent = [Reference(**{"reference": "/".join(["Specimen", parent.id])})]
                if fhir_specimen not in all_fhir_specimens:
                    all_fhir_specimens.append(fhir_specimen)


def get_disease_type_snomed_code(disease_text) -> CodeableConcept | None:
    _snomed_coding = None
    for d in disease_types:
        if disease_text in d['value']:
            if d['sctid']:
                code = None
                if not isinstance(d['sctid'], str):
                    code = str(d['sctid'])
                    display = str(d['value'])
                else:
                    code = d['sctid']
                    display = d['value']

                _snomed_coding = CodeableConcept(**{"coding": [{'system': 'http://snomed.info/sct',
                                                                'display': display,
                                                                'code': code}]})
    return _snomed_coding


# Case ---------------------------------------------------------------
# load case mapped key values
# cases = utils.load_ndjson("./tests/fixtures/case/case_key.ndjson")
# case = cases[0]

def assign_fhir_for_case(case, disease_types=disease_types, primary_sites=primary_sites, data_dict=data_dict,
                         race=race, ethnicity=ethnicity):
    # create patient **
    project_id = "GDC"
    NAMESPACE_GDC = uuid3(NAMESPACE_DNS, 'gdc.cancer.gov')

    patient = Patient.model_construct()

    patient_id_identifier = Identifier.model_construct()
    patient_id_identifier.value = case['Patient.id']
    patient_id_identifier.system = "".join(["https://gdc.cancer.gov/", "case_id"])
    patient_id_identifier.use = "official"

    patient.id = utils.mint_id(identifier=patient_id_identifier, resource_type="Patient", project_id=project_id,
                               namespace=NAMESPACE_GDC)

    treatments_med = []
    treatments_medadmin = []
    observations = []
    condition_observations = []
    obs_survey = []
    diagnosis_code = None

    if 'Patient.identifier' in case.keys() and case['Patient.identifier'] and re.match(r"^[A-Za-z0-9\-.]+$",
                                                                                       case['Patient.identifier']):
        patient_submitter_id_identifier = Identifier.model_construct()
        patient_submitter_id_identifier.value = case['Patient.identifier']
        patient_submitter_id_identifier.system = "".join(["https://gdc.cancer.gov/", "case_submitter_id"])
        patient_submitter_id_identifier.use = "secondary"

        patient.identifier = [patient_submitter_id_identifier, patient_id_identifier]
    else:
        patient.identifier = [patient_id_identifier]

    if 'demographic' in case.keys() and 'Patient.birthDate' in case['demographic']:
        if case['demographic']['Patient.birthDate']:
            birth_year_observation = copy.deepcopy(diagnosis_survey)
            birth_year_observation_identifier = Identifier(
                **{
                    "system": "".join(["https://gdc.cancer.gov/", "year_of_birth"]),
                    "value": "/".join([patient.id, str(case['demographic']['Patient.birthDate'])]),
                    "use": "official"
                }
            )
            birth_year_observation_id = utils.mint_id(
                identifier=[birth_year_observation_identifier, patient_id_identifier], resource_type="Observation",
                project_id=project_id,
                namespace=NAMESPACE_GDC)

            birth_year_observation["id"] = birth_year_observation_id
            birth_year_observation["identifier"] = [birth_year_observation_identifier]
            birth_year_observation["code"] = {
                "coding": [
                    {
                        "system": "https://ontobee.org/",
                        "code": "NCIT_C83164",
                        "display": "Year of Birth"
                    }
                ]
            }
            birth_year_observation["subject"] = {
                "reference": "/".join(["Patient", patient.id])
            }
            birth_year_observation["focus"] = [{
                "reference": "/".join(["Patient", patient.id])
            }]
            birth_year_observation["valueQuantity"] = {
                "value": int(case['demographic']['Patient.birthDate']),
                "unit": "year",
                "system": "http://unitsofmeasure.org",
                "code": "a"
            }
            obs_survey.append(birth_year_observation)

    patient_gender = None
    if 'demographic' in case.keys() and 'Patient.gender' in case['demographic']:
        for g in gender:
            if g['value'] == case['demographic']['Patient.gender']:
                patient_gender = g['fhir_display']

    patient.gender = patient_gender

    race_ethnicity_sex = []
    if patient_gender:
        female = {"url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex", "valueCode": "F"}
        male = {"url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex", "valueCode": "M"}

        if patient_gender == 'female':
            race_ethnicity_sex.append(female)
        elif patient_gender == 'male':
            race_ethnicity_sex.append(male)

    if 'demographic' in case.keys() and 'Patient.deceasedBoolean' in case['demographic']:
        if case['demographic']['Patient.deceasedBoolean'] == "Alive":
            patient.deceasedBoolean = False
        elif case['demographic']['Patient.deceasedBoolean'] == "Dead":
            patient.deceasedBoolean = True

    if 'demographic' in case.keys() and 'Patient.deceasedDateTime' in case['demographic']:
        year_of_death = case['demographic']['Patient.deceasedDateTime']
        if year_of_death:
            year_of_death_observation = copy.deepcopy(diagnosis_survey)
            year_of_death_identifier = Identifier(
                **{
                    "system": "".join(["https://gdc.cancer.gov/", "year_of_death"]),
                    "value": "/".join([patient.id, str(year_of_death)]),
                    "use": "official"
                }
            )
            year_of_death_observation_id = utils.mint_id(
                identifier=[year_of_death_identifier, patient_id_identifier], resource_type="Observation",
                project_id=project_id,
                namespace=NAMESPACE_GDC)

            year_of_death_observation["id"] = year_of_death_observation_id
            year_of_death_observation["identifier"] = [year_of_death_identifier]
            year_of_death_observation["code"] = {
                "coding": [
                    {
                        "system": "https://ontobee.org/",
                        "code": "NCIT_C156426",
                        "display": "Year of Death"
                    }
                ]
            }
            year_of_death_observation["subject"] = {
                "reference": "/".join(["Patient", patient.id])
            }
            year_of_death_observation["focus"] = [{
                "reference": "/".join(["Patient", patient.id])
            }]
            year_of_death_observation["valueQuantity"] = {
                "value": int(year_of_death),
                "unit": "year",
                "system": "http://unitsofmeasure.org",
                "code": "a"
            }
            obs_survey.append(year_of_death_observation)

    if 'demographic' in case.keys() and 'Extension.extension:USCoreRaceExtension' in case['demographic'].keys():
        #  race and ethnicity
        # https://build.fhir.org/ig/HL7/US-Core/ValueSet-omb-race-category.html
        # https://build.fhir.org/ig/HL7/US-Core/ValueSet-omb-ethnicity-category.html

        race_ext = Extension.model_construct()
        race_ext.url = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
        race_ext.valueString = str(case['demographic']['Extension.extension:USCoreRaceExtension'])

        race_code = ""
        race_display = ""
        race_system = ""
        for r in race:
            if r['value'] in case['demographic']['Extension.extension:USCoreRaceExtension'] and re.match(
                    r"[ \r\n\t\S]+", r['ombCategory-code']):
                race_ext.valueString = str(r['value'])

        if race_ext not in race_ethnicity_sex:
            race_ethnicity_sex.append(race_ext)

    if 'demographic' in case.keys() and 'Extension:extension.USCoreEthnicity' in case['demographic'].keys():
        ethnicity_ext = Extension.model_construct()
        ethnicity_ext.url = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"

        ethnicity_code = ""
        ethnicity_display = ""
        ethnicity_system = ""
        for e in ethnicity:
            if e['value'] in case['demographic']['Extension:extension.USCoreEthnicity']:
                ethnicity_ext.valueString = str(e['value'])

        if ethnicity_ext not in race_ethnicity_sex:
            race_ethnicity_sex.append(ethnicity_ext)

    if 'demographic' in case.keys() and 'Patient.extension.age' in case['demographic'].keys():
        # alternative way(s) of defining age vs birthDate in patient field
        # "url": "http://hl7.org/fhir/us/icsr-ae-reporting/StructureDefinition/icsr-ext-ageattimeofonset"
        if case['demographic']['Patient.extension.age']:
            age_at_index = case['demographic']['Patient.extension.age']
            age = {"url": "http://hl7.org/fhir/SearchParameter/patient-extensions-Patient-age",
                   'valueQuantity': {"value": int(age_at_index)}}
            if age not in race_ethnicity_sex:
                race_ethnicity_sex.append(age)

    if race_ethnicity_sex:
        patient.extension = race_ethnicity_sex

    # gdc project for patient
    research_studies = []
    rs, rs_parent = create_researchstudy(project_data=case['ResearchStudy'])
    research_studies.append(rs)
    research_studies.append(rs_parent)

    study_ref = Reference(**{"reference": "/".join(["ResearchStudy", rs.id])})
    subject_ref = Reference(**{"reference": "/".join(["Patient", patient.id])})

    # create researchSubject to link Patient --> ResearchStudy
    research_subject = ResearchSubject.model_construct()
    # research_subject.status = "".join(['unknown-', case['ResearchSubject.status']])
    research_subject.status = "active"
    research_subject.study = study_ref
    research_subject.subject = subject_ref
    research_subject.identifier = [patient_id_identifier]
    research_subject.id = utils.mint_id(
        identifier=patient_id_identifier,
        resource_type="ResearchSubject",
        project_id=project_id,
        namespace=NAMESPACE_GDC)

    # create Organization + Practitioner**
    practitioner_ref = None
    organization_ref = None
    practitioners = []
    organizations = []
    if 'tissue_source_site' in case.keys():
        # in R5 must go from Practitioner -> Organization - this is changed in R6.
        tss_secondary_identifiers = []
        _tss_value = case['tissue_source_site']['Organization.id']
        tss_pi_identifier = Identifier(**{"system": "".join(["https://gdc.cancer.gov/", "tissue_source_site"]),
                                          "value": "-".join([case['tissue_source_site']['Organization.id'], "PI"]),
                                          "use": "official"})
        tss_pi_id = utils.mint_id(identifier=tss_pi_identifier, resource_type="Practitioner", project_id=project_id,
                                  namespace=NAMESPACE_GDC)
        tss_identifier = Identifier(**{"system": "".join(["https://gdc.cancer.gov/", "tissue_source_site"]),
                                       "value": case['tissue_source_site']['Organization.id'],
                                       "use": "official"})
        tss_secondary_identifiers.append(tss_identifier)
        tss_secondary_identifier = None
        if 'Organization.identifier.secondary' in case['tissue_source_site'].keys() and case['tissue_source_site'][
            'Organization.identifier.secondary']:
            tss_secondary_identifier = Identifier(**{"system": "".join(["https://gdc.cancer.gov/", "bcr_id"]),
                                           "value": case['tissue_source_site']['Organization.identifier.secondary'],
                                           "use": "secondary"})
            tss_secondary_identifiers.append(tss_secondary_identifier)
        tss_id = utils.mint_id(identifier=tss_identifier, resource_type="Organization", project_id=project_id,
                               namespace=NAMESPACE_GDC)

        if tss_id:
            organization_ref = Reference(**{"reference": "/".join(["Organization", tss_id])})

        if tss_id:
            if tss_pi_id:
                practitioner_ref = Reference(**{"reference": "/".join(["Practitioner", tss_pi_id])})
                practitioner = Practitioner(**{"id": tss_pi_id, "identifier": [tss_pi_identifier],
                                               "qualification": [{"issuer": organization_ref,
                                                                  "code": CodeableConcept(**{"coding": [{"code": "PHD",
                                                                                                         "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                                                                                                         "display": "Doctor of Philosophy"}]})}]})
                if practitioner:
                    practitioners.append(practitioner)

                organization_name = None
                if 'Organization.name' in case['tissue_source_site'].keys() and case['tissue_source_site']['Organization.name']:
                    organization_name = str(case['tissue_source_site']['Organization.name'])

                organization = Organization(**{"id": tss_id, "identifier": tss_secondary_identifiers, "name": organization_name})

                if organization:
                    organizations.append(organization)

    observation = None
    observation_ref = None
    gdc_condition_annotation = None
    condition_codes_list = []
    staging_observations = []

    if 'demographic' in case.keys() and 'Observation.survey.days_to_death' in case['demographic'].keys() and \
            case['demographic'][
                'Observation.survey.days_to_death']:

        days_to_death = case['demographic'].get('Observation.survey.days_to_death', None)
        if days_to_death is not None:
            observation_days_to_death_identifier = Identifier(
                **{
                    "system": "".join(["https://gdc.cancer.gov/", "days_to_death"]),
                    "value": "/".join([patient.id, str(days_to_death)]),
                    "use": "official"
                }
            )
            observation_days_to_death_id = utils.mint_id(
                identifier=[observation_days_to_death_identifier, patient_id_identifier], resource_type="Observation",
                project_id=project_id,
                namespace=NAMESPACE_GDC)

            days_to_death_obervation = copy.deepcopy(diagnosis_survey)
            days_to_death_obervation["id"] = observation_days_to_death_id
            days_to_death_obervation["identifier"] = [observation_days_to_death_identifier]
            days_to_death_obervation["code"] = {
                "coding": [
                    {
                        "system": "https://ontobee.org/",
                        "code": "NCIT_C156419",
                        "display": "Days between Diagnosis and Death"
                    }
                ]
            }
            days_to_death_obervation["subject"] = {
                "reference": "/".join(["Patient", patient.id])
            }
            days_to_death_obervation["focus"] = [{
                "reference": "/".join(["Patient", patient.id])
            }]
            days_to_death_obervation["valueQuantity"] = {
                "value": int(case['demographic'][
                                 'Observation.survey.days_to_death']),
                "unit": "days",
                "system": "http://unitsofmeasure.org",
                "code": "d"
            }

            obs_survey.append(days_to_death_obervation)

    if 'demographic' in case.keys() and 'Observation.survey.days_to_birth' in case['demographic'].keys():
        days_to_birth = case['demographic'].get('Observation.survey.days_to_birth', None)

        if days_to_birth is not None:
            days_to_birth_identifier = Identifier(
                **{
                    "system": "".join(["https://gdc.cancer.gov/", "days_to_birth"]),
                    "value": "/".join([patient.id, str(days_to_birth)]),
                    "use": "official"
                }
            )
            days_to_birth_id = utils.mint_id(
                identifier=[days_to_birth_identifier, patient_id_identifier], resource_type="Observation",
                project_id=project_id,
                namespace=NAMESPACE_GDC)

            days_to_birth_obervation = copy.deepcopy(diagnosis_survey)
            days_to_birth_obervation["id"] = days_to_birth_id
            days_to_birth_obervation["identifier"] = [days_to_birth_identifier]
            days_to_birth_obervation["code"] = {
                "coding": [
                    {
                        "system": "https://ontobee.org/",
                        "code": "NCIT_C156418",
                        "display": "Days Between Birth and Diagnosis"
                    }
                ]
            }
            days_to_birth_obervation["subject"] = {
                "reference": "/".join(["Patient", patient.id])
            }
            days_to_birth_obervation["focus"] = [{
                "reference": "/".join(["Patient", patient.id])
            }]
            days_to_birth_obervation["valueQuantity"] = {
                "value": case['demographic'][
                    'Observation.survey.days_to_birth'],
                "unit": "days",
                "system": "http://unitsofmeasure.org",
                "code": "d"
            }

            obs_survey.append(days_to_birth_obervation)

    if 'diagnoses' in case.keys() and isinstance(case['diagnoses'], list):
        case['diagnoses'] = {k: v for d in case['diagnoses'] for k, v in d.items()}

    if 'diagnoses' in case.keys() and 'Condition.id' in case['diagnoses'].keys():
        # create Observation **
        observation = Observation.model_construct()
        observation.status = 'final'

        observation_identifier = Identifier(**{"system": "".join(["https://gdc.cancer.gov/", "diagnosis_id"]),
                                               "value": case['diagnoses']['Condition.id'],
                                               "use": "official"})
        observation.id = utils.mint_id(identifier=[observation_identifier, patient_id_identifier],
                                       resource_type="Observation",
                                       project_id=project_id,
                                       namespace=NAMESPACE_GDC)

        observation.identifier = [observation_identifier]
        observation.subject = subject_ref
        observation.category = [{
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "encounter-diagnosis",
                    "display": "Encounter Diagnosis"
                },
                {
                    "system": "http://snomed.info/sct",
                    "code": "439401001",
                    "display": "Diagnosis"
                }
            ]
        }]

        # if encounter_ref:
        #     observation.encounter = encounter_ref

        observation_code = CodeableConcept.model_construct()
        if 'Condition.coding_icd_10_code' in case['diagnoses']:
            system = "https://terminology.hl7.org/5.1.0/NamingSystem-icd10CM.html"
            code = case['diagnoses']['Condition.coding_icd_10_code']
            icd10code = icd10.find(case['diagnoses']['Condition.coding_icd_10_code'])
            if icd10code:
                display = icd10code.description
                icd10_annotation = {'system': system, 'display': display, 'code': code}
                condition_codes_list.append(icd10_annotation)

        # not all conditions of GDC have enumDef for it's resource code/system in data dictionary
        if 'Condition.code_primary_diagnosis' in case['diagnoses'].keys() and case['diagnoses'][
            'Condition.code_primary_diagnosis']:
            diagnosis_code = case['diagnoses']['Condition.code_primary_diagnosis']
            condition_codes_list.append({"code": diagnosis_code,
                                         "display": diagnosis_code,
                                         "system": "".join(["https://gdc.cancer.gov/", "primary_diagnosis"])})

            if case['diagnoses']['Condition.code_primary_diagnosis'] in \
                    data_dict["clinical"]["diagnosis"]["properties"]["primary_diagnosis"]["enumDef"].keys():
                diagnosis_display = case['diagnoses']['Condition.code_primary_diagnosis']
                ncit_condition_display = \
                    data_dict["clinical"]["diagnosis"]["properties"]["primary_diagnosis"]["enumDef"][diagnosis_display][
                        "termDef"]["term"]
                ncit_condition_code = \
                    data_dict["clinical"]["diagnosis"]["properties"]["primary_diagnosis"]["enumDef"][diagnosis_display][
                        "termDef"]["term_id"]
                ncit_condition = {"system": "https://ncit.nci.nih.gov", "display": ncit_condition_display,
                                  "code": ncit_condition_code}
                condition_codes_list.append(ncit_condition)

                mondo = [d["mondo_id"] for d in ncit2mondo if d["ncit_id"] == ncit_condition_code]
                if mondo:
                    mondo_code = str(mondo[0])
                    mondo_display = ncit_condition_display
                    mondo_coding = {'system': "https://www.ebi.ac.uk/ols4/ontologies/mondo", 'display': mondo_display,
                                    'code': mondo_code}
                    condition_codes_list.append(mondo_coding)

        if not condition_codes_list:
            log_output_diag = f"Diagnosis for {patient.identifier} doesn't exist!\n"
            with open('output.log', 'a') as f:
                f.write(log_output_diag)

        observation_code.coding = condition_codes_list
        observation.code = observation_code
        observation_ref = Reference(**{"reference": "/".join(["Observation", observation.id])})

    survey_updated_datetime_component = None
    if 'diagnoses' in case.keys() and "Observation.survey.updated_datetime" in case['diagnoses'].keys() and \
            case['diagnoses'][
                "Observation.survey.updated_datetime"]:
        survey_updated_datetime_component = utils.get_component('updated_datetime', value=case['diagnoses'][
            "Observation.survey.updated_datetime"],
                                                                component_type='dateTime',
                                                                system="https://gdc.cancer.gov/demographic")

    if 'diagnoses' in case.keys() and 'Observation.survey.days_to_last_follow_up' in case['diagnoses'].keys() and \
            case['diagnoses'][
                'Observation.survey.days_to_last_follow_up']:
        if case['diagnoses']['Observation.survey.days_to_last_follow_up']:
            observation_days_to_last_follow_up_identifier = Identifier(
                **{"system": "".join(["https://gdc.cancer.gov/", "days_to_last_follow_up"]),
                   "value": str(case['diagnoses']['Observation.survey.days_to_last_follow_up']),
                   "use": "official"})
            observation_days_to_last_follow_up_id = utils.mint_id(
                identifier=[observation_days_to_last_follow_up_identifier, patient_id_identifier],
                resource_type="Observation",
                project_id=project_id,
                namespace=NAMESPACE_GDC)

            days_to_last_follow_up = copy.deepcopy(diagnosis_survey)
            days_to_last_follow_up["category"][0]["coding"][0]["code"] = "exam"
            days_to_last_follow_up["category"][0]["coding"][0]["display"] = "exam"
            days_to_last_follow_up["id"] = observation_days_to_last_follow_up_id
            days_to_last_follow_up["code"] = {
                "coding": [
                    {
                        "system": "https://ontobee.org/",
                        "code": "NCIT_C181065",
                        "display": "Number of Days Between Index Date and Last Follow Up"
                    }
                ]
            }
            days_to_last_follow_up["subject"] = {
                "reference": "/".join(["Patient", patient.id])
            }
            days_to_last_follow_up["focus"] = [{
                "reference": "/".join(["Patient", patient.id])
            }]
            days_to_last_follow_up["valueQuantity"] = {
                "value": int(case['diagnoses']['Observation.survey.days_to_last_follow_up']),
                "unit": "days",
                "system": "http://unitsofmeasure.org",
                "code": "d"
            }

            if survey_updated_datetime_component:
                days_to_last_follow_up['component'] = [survey_updated_datetime_component]
            obs_survey.append(days_to_last_follow_up)

    if 'diagnoses' in case.keys() and 'Observation.survey.days_to_last_known_disease_status' in case[
        'diagnoses'].keys() and \
            case['diagnoses'][
                'Observation.survey.days_to_last_known_disease_status']:
        if case['diagnoses']['Observation.survey.days_to_last_known_disease_status']:
            days_to_last_known_disease_status_identifier = Identifier(
                **{"system": "".join(["https://gdc.cancer.gov/", "days_to_last_known_disease_status"]),
                   "value": str(case['diagnoses']['Observation.survey.days_to_last_known_disease_status']),
                   "use": "official"})
            days_to_last_follow_up_id = utils.mint_id(
                identifier=[days_to_last_known_disease_status_identifier, patient_id_identifier],
                resource_type="Observation",
                project_id=project_id,
                namespace=NAMESPACE_GDC)

            days_to_last_known_disease_status_observation = copy.deepcopy(diagnosis_survey)
            days_to_last_known_disease_status_observation["category"][0]["coding"][0]["code"] = "exam"
            days_to_last_known_disease_status_observation["category"][0]["coding"][0]["display"] = "exam"
            days_to_last_known_disease_status_observation["id"] = days_to_last_follow_up_id
            days_to_last_known_disease_status_observation["code"] = {
                "coding": [
                    {
                        "system": "https://ontobee.org/",
                        "code": "NCIT_C181066",
                        "display": "Number of Days to Last Known Disease Status"
                    }
                ]
            }
            days_to_last_known_disease_status_observation["subject"] = {
                "reference": "/".join(["Patient", patient.id])
            }
            days_to_last_known_disease_status_observation["focus"] = [{
                "reference": "/".join(["Patient", patient.id])
            }]
            days_to_last_known_disease_status_observation["valueQuantity"] = {
                "value": int(case['diagnoses']['Observation.survey.days_to_last_known_disease_status']),
                "unit": "days",
                "system": "http://unitsofmeasure.org",
                "code": "d"
            }

            obs_survey.append(days_to_last_known_disease_status_observation)

    if 'diagnoses' in case.keys() and 'Observation.survey.days_to_diagnosis' in case['diagnoses'].keys() and \
            case['diagnoses'][
                'Observation.survey.days_to_diagnosis']:
        if case['diagnoses']['Observation.survey.days_to_diagnosis']:
            days_to_diagnosis_identifier = Identifier(
                **{"system": "".join(["https://gdc.cancer.gov/", "days_to_diagnosis"]),
                   "value": str(case['diagnoses']['Observation.survey.days_to_diagnosis']),
                   "use": "official"})
            days_to_diagnosis_id = utils.mint_id(
                identifier=[days_to_diagnosis_identifier, patient_id_identifier],
                resource_type="Observation",
                project_id=project_id,
                namespace=NAMESPACE_GDC)

            days_to_diagnosis_observation = copy.deepcopy(diagnosis_survey)
            days_to_diagnosis_observation["category"][0]["coding"][0]["code"] = "exam"
            days_to_diagnosis_observation["category"][0]["coding"][0]["display"] = "exam"
            days_to_diagnosis_observation["id"] = days_to_diagnosis_id
            days_to_diagnosis_observation["code"] = {
                "coding": [
                    {
                        "system": "https://ontobee.org/",
                        "code": "NCIT_C181061",
                        "display": "Number of Days Between Index Date and Diagnosis"
                    }
                ]
            }
            days_to_diagnosis_observation["subject"] = {
                "reference": "/".join(["Patient", patient.id])
            }
            days_to_diagnosis_observation["focus"] = [{
                "reference": "/".join(["Patient", patient.id])
            }]
            days_to_diagnosis_observation["valueQuantity"] = {
                "value": int(case['diagnoses']['Observation.survey.days_to_diagnosis']),
                "unit": "days",
                "system": "http://unitsofmeasure.org",
                "code": "d"
            }

            obs_survey.append(days_to_diagnosis_observation)

    condition = None  # normal tissue don't/shouldn't  have diagnoses or condition
    body_structure = None
    if 'diagnoses' in case.keys() and 'Condition.id' in case['diagnoses'].keys():
        # create Condition - for each diagnosis_id there is. relation: condition -- assessment --> observation
        condition = Condition.model_construct()
        condition_identifier = Identifier(**{"system": "".join(["https://gdc.cancer.gov/", "diagnosis_id"]),
                                             "value": case['diagnoses']['Condition.id'],
                                             "use": "official"})
        condition.id = utils.mint_id(identifier=condition_identifier, resource_type="Condition", project_id=project_id,
                                     namespace=NAMESPACE_GDC)

        condition.category = [CodeableConcept(**{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "encounter-diagnosis",
            "display": "Encounter Diagnosis"
        },
            {
                "system": "http://snomed.info/sct",
                "code": "439401001",
                "display": "Diagnosis"
            }]})]

        if 'Condition.identifier' in case.keys() and case['Condition.identifier']:
            condition.identifier = [Identifier(**{"value": case['Condition.identifier'][0], "system": "".join(
                ["https://gdc.cancer.gov/", "submitter_diagnosis_id"]), "use": "official"})]

        # if gdc_condition_annotation:
        #     cc = CodeableConcept.model_construct()
        #     cc.coding = [gdc_condition_annotation]
        #     condition.code = cc

        condition_clinicalstatus_code = CodeableConcept.model_construct()
        condition_clinicalstatus_code.coding = [
            {"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "display": "unknown",
             "code": "unknown"}]
        condition.clinicalStatus = condition_clinicalstatus_code

        condition.subject = subject_ref
        # condition.encounter = encounter_ref

        if diagnosis_code:
            _snomed_diagnosis_code = get_disease_type_snomed_code(diagnosis_code)
            if _snomed_diagnosis_code:
                condition.code = _snomed_diagnosis_code
            else:
                condition.code = CodeableConcept(**{"coding": [{"code": diagnosis_code,
                                                                "display": diagnosis_code,
                                                                "system": "".join(["https://gdc.cancer.gov/",
                                                                                   "primary_diagnosis"])}]})

        if 'diagnoses' in case.keys() and 'Condition.onsetAge' in case['diagnoses'].keys() and case['diagnoses'][
            'Condition.onsetAge']:
            # https://build.fhir.org/valueset-age-units.html
            condition.onsetAge = {
                "value": case['diagnoses']['Condition.onsetAge'],
                "unit": "days",
                "system": "http://unitsofmeasure.org",
                "code": "d"
            }

        # condition.bodySite <-- primary_site snomed
        l_body_site = []
        bd_coding = []
        body_struct = None
        for body_site in case['ResearchStudy']['Condition.bodySite']:
            # print("body_site", body_site)
            for p in primary_sites:
                if not 'sctid' in p.keys():
                    code = "0000"
                elif not p['sctid']:
                    code = "0000"
                else:
                    code = p['sctid']
                if body_site in p['value'] and 'sctid' in p.keys():
                    if code == "0000":
                        print(f"Condition body-site code for {body_site} for patient-id: {patient.id} not found.")
                    l_body_site.append({'system': "http://snomed.info/sct", 'display': p['value'], 'code': code})
                    body_struct = {'system': "http://snomed.info/sct", 'display': p['value'], 'code': code}
                    bd_coding.append(body_struct)

        body_struct_ident = None
        if body_struct['display']:
            body_struct_ident = Identifier(
                **{"value": body_struct['display'], "system": "".join(["https://gdc.cancer.gov/", "primary_site"])})
        body_structure = BodyStructure(
            **{"id": utils.mint_id(identifier=[patient_id_identifier, body_struct_ident], resource_type="BodyStructure",
                                   project_id=project_id,
                                   namespace=NAMESPACE_GDC),
               "identifier": [patient_id_identifier, body_struct_ident],
               "includedStructure": [BodyStructureIncludedStructure(**{"structure": {"coding": bd_coding}})],
               "patient": subject_ref
               })

        cc_body_site = CodeableConcept.model_construct()
        cc_body_site.coding = l_body_site
        condition.bodySite = [cc_body_site]
        diagnosis_content_bool = False
        if 'diagnoses' in case.keys():
            # condition and observation staging
            #  grouping for observation.code https://build.fhir.org/ig/HL7/fhir-mCODE-ig/ValueSet-mcode-tnm-stage-group-staging-type-vs.html
            # https://build.fhir.org/ig/hl7-eu/pcsp/StructureDefinition-mcode-cancer-stage-group.html
            staging_list = []
            parent_stage_observation = Observation(**{
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "laboratory",
                                "display": "Laboratory"
                            }
                        ],
                        "text": "Laboratory"
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "1222593009",
                            "display": "American Joint Committee on Cancer pathological stage group allowable value"
                        }
                    ]
                },
                "subject": {
                    "reference": f"Patient/{patient.id}"
                },
                "focus": [
                    {
                        "reference": f"Condition/{condition.id}"
                    }
                ]
            })

            # print("case['diagnoses']", case['diagnoses'])
            for key, value in case['diagnoses'].items():
                if 'Condition.stage_' in key and value:
                    case_stage_display = value
                    staging_name = key.replace('Condition.stage_', '')

                    sctid_code = "0000"
                    stage_type_sctid_code = "0000"
                    assessment_reference = None
                    for dict_item in cancer_pathological_staging:
                        if case['diagnoses'][key] == dict_item['value']:
                            sctid_code = dict_item['sctid']
                            stage_type_sctid_code = dict_item['stage_type_sctid']

                            if staging_name in "ajcc_pathologic_stage":
                                stage_parent_obs_identifier = Identifier(
                                    **{"system": "".join(["https://gdc.cancer.gov/", "ajcc_pathologic_stage"]),
                                       "value": f"{patient.identifier[0]}-{condition.identifier[0]}-{dict_item['value']}"})
                                parent_stage_observation.identifier = [stage_parent_obs_identifier]
                                parent_stage_observation.id = utils.mint_id(identifier=stage_parent_obs_identifier,
                                                                            resource_type="Observation",
                                                                            project_id=project_id,
                                                                            namespace=NAMESPACE_GDC)

                                assessment_reference = Reference(
                                    **{"reference": f"Observation/{parent_stage_observation.id}"})
                                parent_stage_observation.valueCodeableConcept = {
                                    "coding": [
                                        {
                                            "system": "http://snomed.info/sct",
                                            "code": str(dict_item['sctid']),
                                            "display": dict_item['sctid_display']
                                        }
                                    ],
                                    "text": dict_item['value']
                                }
                            else:
                                stage_obs = Observation(**{
                                    "status": "final",
                                    "category": [
                                        {
                                            "coding": [
                                                {
                                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                                    "code": "laboratory",
                                                    "display": "Laboratory"
                                                }
                                            ],
                                            "text": "Laboratory"
                                        }
                                    ],
                                    "code": {
                                        "coding": [
                                            {
                                                "system": "http://snomed.info/sct",
                                                "code": dict_item['stage_type_sctid'],
                                                "display": dict_item['stage_type_display']
                                            }
                                        ]
                                    },
                                    "subject": {
                                        "reference": f"Patient/{patient.id}"
                                    },
                                    "focus": [
                                        {
                                            "reference": f"Condition/{condition.id}"
                                        }
                                    ],
                                    "valueCodeableConcept": {
                                        "coding": [
                                            {
                                                "system": "http://snomed.info/sct",
                                                "code": str(dict_item['sctid']),
                                                "display": dict_item['sctid_display']
                                            }
                                        ],
                                        "text": dict_item['value']
                                    }
                                })
                                stage_obs_identifier = Identifier(
                                    **{"system": "".join(["https://gdc.cancer.gov/", "ajcc_pathologic_stage"]),
                                       "value": f"{patient.identifier[0]}-{condition.identifier[0]}-{dict_item['value']}",
                                       "use": "official"})
                                stage_obs.identifier = [stage_obs_identifier]
                                stage_obs.id = utils.mint_id(identifier=stage_obs_identifier,
                                                             resource_type="Observation", project_id=project_id,
                                                             namespace=NAMESPACE_GDC)
                                assessment_reference = Reference(**{"reference": f"Observation/{stage_obs.id}"})
                                staging_observations.append(stage_obs)

                    if not parent_stage_observation.id:
                        stage_parent_obs_identifier = Identifier(
                            **{"system": "".join(["https://gdc.cancer.gov/", "ajcc_pathologic_stage"]),
                               "value": f"{patient.identifier[0]}-{condition.identifier[0]}-Not Available",
                               "use": "official"})
                        parent_stage_observation.identifier = [stage_parent_obs_identifier]
                        parent_stage_observation.id = utils.mint_id(identifier=stage_parent_obs_identifier,
                                                                    resource_type="Observation",
                                                                    project_id=project_id,
                                                                    namespace=NAMESPACE_GDC)
                    # assign as parent even if main stage was not defined
                    stage_obs_references = [Reference(**{"reference": f"Observation/{s.id}"}) for s in
                                            staging_observations]
                    parent_stage_observation.hasMember = stage_obs_references
                    staging_observations.append(parent_stage_observation)

                    cc_stage_type = CodeableConcept.model_construct()
                    cc_stage_type.coding = [{'system': "https://cadsr.cancer.gov/",
                                             'display': case['diagnoses'][key],
                                             'code': str(data_dict['clinical']['diagnosis']['properties'][staging_name][
                                                             'termDef'][
                                                             'cde_id'])},
                                            {'system': "http://snomed.info/sct",
                                             'display': case['diagnoses'][key],
                                             'code': str(stage_type_sctid_code)}
                                            ]
                    if sctid_code in "0000":
                        log_output_diag = f"Condition stage - sctid_code codeableConcept code in sctid_code for {case['diagnoses'][key]} not found! {case_stage_display}\n"
                        with open('output.log', 'a') as f:
                            f.write(log_output_diag)

                    if stage_type_sctid_code in "0000":
                        log_output_diag = f"Condition stage - stage_type_sctid_code codeableConcept code in stage_type_sctid_code for {case['diagnoses'][key]} not found! {case_stage_display}\n"
                        with open('output.log', 'a') as f:
                            f.write(log_output_diag)

                    if case_stage_display and case_stage_display in \
                            data_dict['clinical']['diagnosis']['properties'][staging_name]['enumDef'].keys():
                        code = \
                            data_dict['clinical']['diagnosis']['properties'][staging_name]['enumDef'][
                                case_stage_display][
                                'termDef']['cde_id']
                    else:
                        code = "0000"

                    if case['diagnoses'][key]:
                        display = case['diagnoses'][key]
                    else:
                        display = "replace-me"
                        diagnosis_content_bool = True

                    if not re.match(r"^[^\s]+(\s[^\s]+)*$", sctid_code):
                        sctid_code = "0000"

                    cc_stage = CodeableConcept.model_construct()
                    cc_stage.coding = [{'system': "https://ncit.nci.nih.gov",
                                        'display': display,
                                        'code': str(code)
                                        }]

                    cc_stage_sctid = CodeableConcept.model_construct()
                    cc_stage_sctid.coding = [{'system': "http://snomed.info/sct",
                                              'display': display,
                                              'code': str(sctid_code)}]

                    condition_stage = ConditionStage.model_construct()
                    condition_stage.summary = cc_stage
                    condition_stage.type = cc_stage_type
                    condition_stage.assessment = [assessment_reference]

                    if observation_ref:
                        if condition_stage.assessment:
                            condition_stage.assessment.append(observation_ref)
                        else:
                            condition_stage.assessment = [observation_ref]

                    staging_list.append(condition_stage)

                if diagnosis_content_bool:
                    log_output_diag = f"Diagnosis codableConcept display of {key} for patient-id: {patient.id} doesn't exist or was not found!\n"
                    with open('output.log', 'a') as f:
                        f.write(log_output_diag)

            if "Observation.code.nci_tumor_grade" in case["diagnoses"].keys() and case["diagnoses"][
                "Observation.code.nci_tumor_grade"]:
                # temp fix for demo
                grade = ConditionStage(**{"type": CodeableConcept(**{"coding": [
                    {"code": "2785839", "system": "https://cadsr.cancer.gov",
                     "display": "neoplasm_histologic_grade"}]}),
                                          "summary": CodeableConcept(**{"coding": [
                                              {"code": "2785839", "system": "https://cadsr.cancer.gov",
                                               "display": case["diagnoses"]["Observation.code.nci_tumor_grade"]}]}),
                                          "assessment": [observation_ref]})
                staging_list.append(grade)

                grade_observation = Observation(**{"status": "final",
                                                   "category": [
                                                       {
                                                           "coding": [
                                                               {
                                                                   "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                                                   "code": "laboratory",
                                                                   "display": "Laboratory"
                                                               }
                                                           ],
                                                           "text": "Laboratory"
                                                       }
                                                   ],
                                                   "code": {
                                                       "coding": [
                                                           {
                                                               "system": "https://cadsr.cancer.gov",
                                                               "code": "2785839",
                                                               "display": "neoplasm_histologic_grade"
                                                           }
                                                       ]
                                                   },
                                                   "subject": {
                                                       "reference": f"Patient/{patient.id}"
                                                   },
                                                   "focus": [
                                                       {
                                                           "reference": f"Condition/{condition.id}"
                                                       }
                                                   ],
                                                   "valueCodeableConcept": {
                                                       "coding": [
                                                           {
                                                               "system": "http://snomed.info/sct",
                                                               "code": "2785839",
                                                               "display": case["diagnoses"][
                                                                   "Observation.code.nci_tumor_grade"]
                                                           }
                                                       ],
                                                       "text": case["diagnoses"]["Observation.code.nci_tumor_grade"]
                                                   }
                                                   })
                grade_obs_identifier = Identifier(
                    **{"system": "".join(["https://gdc.cancer.gov/", "ajcc_pathologic_stage"]),
                       "value": f"{patient.identifier[0]}-{condition.identifier[0]}-{case["diagnoses"]["Observation.code.nci_tumor_grade"]}",
                       "use": "official"})
                grade_observation.identifier = [grade_obs_identifier]
                grade_observation.id = utils.mint_id(identifier=grade_obs_identifier,
                                                     resource_type="Observation", project_id=project_id,
                                                     namespace=NAMESPACE_GDC)
                staging_observations.append(grade_observation)
                if parent_stage_observation.valueCodeableConcept:
                    parent_stage_observation.hasMember.append(
                        Reference(**{"reference": f"Observation/{grade_observation.id}"}))

            condition.stage = staging_list
            observation.focus = [Reference(**{"reference": "/".join(["Condition", condition.id])})]
            condition_observations.append(orjson.loads(observation.model_dump_json()))

            # create medication administration and medication
            treatment_content_bool = False
            if 'treatments' in case['diagnoses'].keys():

                for treatment in case['diagnoses']['treatments']:
                    # https://build.fhir.org/ig/HL7/fhir-mCODE-ig/artifacts.html

                    if 'Medication.code' in treatment.keys() and treatment['Medication.code']:
                        therapeutic_agents_display = treatment['Medication.code']
                        theraputic_agents_code = treatment['Medication.code']  # TODO: pull from chembl
                        theraputic_agents_system = "".join(["https://gdc.cancer.gov/", "therapeutic_agents"])
                    else:
                        therapeutic_agents_display = "Unknown"
                        theraputic_agents_code = "261665006"
                        theraputic_agents_system = "'http://snomed.info/sct'"
                        treatment_content_bool = True

                    med_code = CodeableConcept.model_construct()
                    med_code.coding = [{'system': theraputic_agents_system,
                                        'display': therapeutic_agents_display,
                                        'code': theraputic_agents_code}]

                    med_cr = CodeableReference.model_construct()

                    if therapeutic_agents_display and isinstance(therapeutic_agents_display,
                                                                 str) and therapeutic_agents_display.upper() not in [
                        "UNKNOWN", "NOT REPORTED", "OTHER", "CHEMOTHERAPY", "NOT OTHERWISE SPECIFIED"]:
                        """Medication name exists - create medication and add it to MedicationAdministration.medication.CodeableReference.reference"""
                        med = Medication.model_construct()
                        med_identifier = Identifier(
                            **{"system": "".join(["https://gdc.cancer.gov/", "therapeutic_agents"]),
                               "value": therapeutic_agents_display.upper(),
                               "use": "official"})
                        """
                        # TODO: fetch from chembl - not fetched via query
                        ['NAB-PACLITAXEL','THERAPEUTIC HYDROCORTISONE','LIPOSOMAL IRINOTECAN']
                        [Nab-paclitaxel (Abraxane), HYDROCORTISONE, "IRINOTECAN LIPOSOMAL"]
                        """
                        med.identifier = [med_identifier]
                        med.id = utils.mint_id(identifier=med_identifier, resource_type="Medication",
                                               project_id=project_id,
                                               namespace=NAMESPACE_GDC)

                        med_cr.reference = Reference(**{"reference": "/".join(["Medication", med.id])})
                        med.code = med_code
                        treatments_med.append(med)
                        med_cr.concept = med_code
                    else:
                        med_cr.concept = med_code

                    # if treatment['treatment_or_therapy'] == "yes" then completed, no "not-done"
                    status = "unknown"
                    if 'treatment_or_therapy' in treatment.keys() and treatment['treatment_or_therapy']:
                        if treatment['treatment_or_therapy'] == "yes":
                            status = "completed"
                        if treatment['treatment_or_therapy'] == "no":
                            status = "not-done"
                        if treatment['treatment_or_therapy'] in ["unknown", "not reported"]:
                            status = "unknown"

                    medadmin_category_code = None
                    med_admin_identifier = Identifier(
                        **{"system": "".join(["https://gdc.cancer.gov/", "treatment_id"]),
                           "value": treatment['MedicationAdministration.id'],
                           "use": "official"})
                    if 'MedicationAdministration.treatment_type' in treatment.keys() and treatment[
                        'MedicationAdministration.treatment_type']:
                        medadmin_category_code = CodeableConcept.model_construct()
                        medadmin_category_code.coding = [{'system': "https://cadsr.cancer.gov/onedata/Home.jsp",
                                                          'display': treatment[
                                                              'MedicationAdministration.treatment_type'],
                                                          'code': '5102381'}]
                    if medadmin_category_code:
                        data = {"status": status,
                                "occurenceDateTime": "2019-07-31T21:32:54.724446-05:00",
                                "category": [medadmin_category_code],
                                # placeholder - required fhir field is not required in GDC
                                "medication": med_cr,
                                "subject": Reference(**{"reference": "/".join(["Patient", patient.id])}),
                                "id": treatment['MedicationAdministration.id'],
                                "identifier": [med_admin_identifier]}
                    else:
                        data = {"status": status,
                                "occurenceDateTime": "2019-07-31T21:32:54.724446-05:00",
                                # placeholder - required fhir field is not required in GDC
                                "medication": med_cr,
                                "subject": Reference(**{"reference": "/".join(["Patient", patient.id])}),
                                "id": utils.mint_id(identifier=med_admin_identifier,
                                                    resource_type="MedicationAdministration",
                                                    project_id=project_id,
                                                    namespace=NAMESPACE_GDC),
                                "identifier": [med_admin_identifier]}

                    med_admin = MedicationAdministration(**data)
                    treatments_medadmin.append(med_admin)

    # if observation:
    #     condition_observations.append(orjson.loads(observation.model_dump_json()))

    # exposures
    smoking_observation = []
    if 'exposures' in case.keys():
        if 'Observation.patient.pack_years_smoked' in case['exposures'][0] and case['exposures'][0][
            'Observation.patient.pack_years_smoked']:
            sm_obs = copy.deepcopy(social_histody_smoking_observation)
            # if 'valueQuantity' in sm_obs.keys():
            #    sm_obs.pop('valueQuantity', None)

            sm_ob_identifier = Identifier(
                **{"system": "".join(["https://gdc.cancer.gov/", "exposures.pack_years_smoked"]),
                   "value": case['exposures'][0]['Observation.patient.exposure_id'],
                   "use": "official"})
            sm_obs['id'] = utils.mint_id(identifier=sm_ob_identifier, resource_type="Observation",
                                         project_id=project_id,
                                         namespace=NAMESPACE_GDC)

            sm_obs['subject'] = {"reference": "".join(["Patient/", patient.id])}
            sm_obs['focus'] = [{"reference": "".join(["Patient/", patient.id])}]
            sm_obs['valueQuantity']['value'] = int(case['exposures'][0]['Observation.patient.pack_years_smoked'])
            smoking_observation.append(copy.deepcopy(sm_obs))

        if 'Observation.patient.cigarettes_per_day' in case['exposures'][0] and isinstance(
                case['exposures'][0]['Observation.patient.cigarettes_per_day'], float):
            sm_pd_obs = copy.deepcopy(social_histody_smoking_observation)
            if 'valueInteger' in sm_pd_obs.keys():
                sm_pd_obs.pop('valueInteger', None)
            sm_pd_obs_code = "".join([case['exposures'][0]['Observation.patient.exposure_id'], patient.id,
                                      orjson.loads(study_ref.model_dump_json())['reference'],
                                      'Observation.patient.cigarettes_per_day'])

            sm_pd_obs['id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, sm_pd_obs_code))
            sm_pd_obs['subject'] = {"reference": "".join(["Patient/", patient.id])}
            sm_pd_obs['focus'] = [{"reference": "".join(["Patient/", patient.id])}]
            sm_pd_obs['valueQuantity'] = {
                "value": round(float(case['exposures'][0]['Observation.patient.cigarettes_per_day']), 2)}
            sm_pd_obs['code'] = {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "64218-1",
                        "display": "How many cigarettes do you smoke per day now"
                    }
                ]
            }
            smoking_observation.append(copy.deepcopy(sm_pd_obs))

    # todo: change to alcohol intensity
    # https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=exposure&anchor=alcohol_intensity
    alcohol_observation = []
    if 'exposures' in case.keys():
        if 'Observation.patient.alcohol_history' in case['exposures'][0] and case['exposures'][0][
            'Observation.patient.alcohol_history']:
            al_obs = copy.deepcopy(social_histody_alcohol_observation)
            al_ob_identifier = Identifier(
                **{"system": "".join(["https://gdc.cancer.gov/", "exposures.alcohol_history"]),
                   "value": case['exposures'][0]['Observation.patient.exposure_id'],
                   "use": "official"})
            al_obs['id'] = utils.mint_id(identifier=al_ob_identifier, resource_type="Observation",
                                         project_id=project_id,
                                         namespace=NAMESPACE_GDC)

            al_obs['subject'] = {"reference": "".join(["Patient/", patient.id])}
            al_obs['focus'] = [{"reference": "".join(["Patient/", patient.id])}]
            al_obs['valueString'] = str(case['exposures'][0]['Observation.patient.alcohol_history'])
            alcohol_observation.append(al_obs)

    # create specimen
    specimen_observations = []
    sample_list = None
    slide_list = []
    procedures = []
    if "samples" in case.keys():
        samples = case["samples"]
        all_samples = []
        all_portions = []
        all_analytes = []
        all_aliquots = []

        sample_observations = []
        portion_observations = []
        analyte_observations = []
        aliquot_observations = []
        slides_observations = []

        for sample in samples:
            if 'Specimen.id.sample' in sample.keys() and sample["Specimen.id.sample"]:
                specimen = Specimen.model_construct()
                specimen_identifiers = []
                specimen_identifier = Identifier(
                    **{"system": "".join(["https://gdc.cancer.gov/", "sample_id"]),
                       "value": sample["Specimen.id.sample"],
                       "use": "official"})
                specimen_identifiers.append(specimen_identifier)
                specimen.id = utils.mint_id(identifier=specimen_identifier, resource_type="Specimen",
                                            project_id=project_id,
                                            namespace=NAMESPACE_GDC)

                if "Specimen.identifier" in sample.keys() and sample["Specimen.identifier"]:
                    specimen_submitter_id = Identifier(
                        **{"system": "".join(["https://gdc.cancer.gov/", "submitter_id"]),
                           "value": sample["Specimen.identifier"],
                           "use": "secondary"})
                    specimen_identifiers.append(specimen_submitter_id)

                specimen.identifier = specimen_identifiers

                # add sample procedure
                # procedure = Procedure.model_construct()
                # procedure.status = "completed"
                # procedure.identifier = [Identifier(
                #     **{"system": "".join(["https://gdc.cancer.gov/", "sample_id/patient_id"]),
                #        "value": "/".join([sample["Specimen.id.sample"], patient.id]),
                #        "use": "official"})]
                #
                # procedure.id = utils.mint_id(identifier=procedure.identifier, resource_type="Procedure",
                #                              project_id=project_id,
                #                              namespace=NAMESPACE_GDC)
                #
                # procedure.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})

                # if encounter:
                #     procedure.encounter = Reference(**{"reference": "/".join(["Encounter", encounter.id])})
                # procedures.append(procedure)

                # specimen.collection = SpecimenCollection(
                #     **{"procedure": Reference(**{"reference": "/".join(["Procedure", procedure.id])}),
                #        "collectedDateTime": "2018-08-23T16:32:20.747393-05:00"})

                # alternative way to travers to TSS from practitioner -> organization
                if practitioner_ref:
                    specimen.collection = SpecimenCollection(
                        **{"collector": practitioner_ref})

                if "Specimen.type.sample" in sample.keys():
                    sample_type = CodeableConcept.model_construct()
                    sample_type.coding = [{
                        'system': "https://cadsr.cancer.gov/sample_type",
                        'display': sample["Specimen.type.sample"],
                        'code': "3111302"}]
                    specimen.type = sample_type
                else:
                    # never reached
                    specimen.type = CodeableConcept(**{"coding": [
                        {"code": "unknown", "system": "https://cadsr.cancer.gov/sample_type", "display": "unknown"}]})

                sp = None
                if "Specimen.processing.method" in sample.keys():
                    sample_processing = CodeableConcept.model_construct()
                    sp = SpecimenProcessing.model_construct()
                    sample_processing.coding = [{
                        'system': "https://cadsr.cancer.gov/preservation_method",
                        'display': sample["Specimen.processing.method"],
                        'code': "5432521"}]
                    sp.method = sample_processing
                    specimen.processing = [sp]

                sample_observation_components = []
                c = None
                if "Observation.sample.composition" in sample.keys() and sample["Observation.sample.composition"]:
                    c = utils.get_component('composition', value=sample["Observation.sample.composition"],
                                            component_type='string')
                    sample_observation_components.append(c)
                if "Observation.sample.is_ffpe" in sample.keys() and isinstance(sample["Observation.sample.is_ffpe"],
                                                                                bool):
                    c = utils.get_component('is_ffpe', value=sample["Observation.sample.is_ffpe"],
                                            component_type='bool')
                    sample_observation_components.append(c)

                if "Specimen.type.sample" in sample.keys() and sample["Specimen.type.sample"]:
                    c = utils.get_component('sample_type',
                                            value=sample["Specimen.type.sample"],
                                            component_type='string')
                    sample_observation_components.append(c)

                if "Observation.sample.updated_datetime" in sample.keys() and sample[
                    "Observation.sample.updated_datetime"]:
                    c = utils.get_component('updated_datetime',
                                            value=sample["Observation.sample.updated_datetime"],
                                            component_type='dateTime')
                    sample_observation_components.append(c)

                sample_observation = None
                if sample_observation_components:
                    sample_observation = copy.deepcopy(biospecimen_observation)
                    sample_observation['id'] = utils.mint_id(identifier=specimen_identifier,
                                                             resource_type="Observation",
                                                             project_id=project_id,
                                                             namespace=NAMESPACE_GDC)

                    sample_observation['component'] = sample_observation_components

                    sample_observation['subject'] = {"reference": "/".join(["Patient", patient.id])}
                    sample_observation['specimen'] = {"reference": "/".join(["Specimen", specimen.id])}
                    sample_observation['focus'][0] = {"reference": "/".join(["Specimen", specimen.id])}

                    if sample_observation not in sample_observations:
                        sample_observations.append(copy.deepcopy(sample_observation))

                specimen.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})

                if not specimen_exists(specimen.id, all_samples):
                    all_samples.append(specimen)

                if "slides" in sample.keys():
                    for slide in sample["slides"]:
                        sample_img_study = create_imaging_study(slide=slide, patient=patient, sample=specimen)
                        slide_list.append(sample_img_study)
                """
                add_specimen(dat=sample, name="analytes", id_key="Specimen.id.analyte", has_parent=True,
                             parent=sample, patient=patient, all_fhir_specimens=all_analytes)

                add_specimen(dat=sample, name="aliquots", id_key="Specimen.id.aliquot", has_parent=True,
                             parent=sample, patient=patient, all_fhir_specimens=all_aliquots)
                """

                if "portions" in sample.keys():
                    for portion in sample['portions']:
                        if "Specimen.id.portion" in portion.keys():

                            portion_specimen = Specimen.model_construct()
                            portion_specimen.type = specimen.type  # inherits type from initial sample

                            portion_specimen_identifier = Identifier(
                                **{"system": "".join(["https://gdc.cancer.gov/", "portion_id"]),
                                   "value": portion["Specimen.id.portion"],
                                   "use": "official"})
                            portion_specimen.id = utils.mint_id(identifier=portion_specimen_identifier,
                                                                resource_type="Specimen",
                                                                project_id=project_id,
                                                                namespace=NAMESPACE_GDC)
                            portion_specimen.identifier = [portion_specimen_identifier]

                            portion_specimen.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})
                            portion_specimen.parent = [Reference(**{"reference": "/".join(["Specimen", specimen.id])})]

                            if practitioner_ref:
                                portion_specimen.collection = SpecimenCollection(
                                    **{"collector": practitioner_ref})

                            portion_specimen.processing = [sp]

                            if not specimen_exists(portion_specimen.id, all_portions):
                                all_portions.append(portion_specimen)

                            portions_observation_components = []
                            if "Observation.portions.weight" in portion.keys() and portion[
                                "Observation.portions.weight"]:
                                c = utils.get_component('weight', value=portion["Observation.portions.weight"],
                                                        component_type='float')
                                portions_observation_components.append(c)
                            if "Observation.portions.is_ffpe" in portion.keys() and isinstance(
                                    portion["Observation.portions.is_ffpe"], bool):
                                c = utils.get_component('is_ffpe', value=portion["Observation.portions.is_ffpe"],
                                                        component_type='bool')
                                portions_observation_components.append(c)

                            if "Specimen.type.sample" in sample.keys() and sample["Specimen.type.sample"]:
                                c = utils.get_component('sample_type',
                                                        value=sample["Specimen.type.sample"],
                                                        component_type='string')
                                portions_observation_components.append(c)

                            if "Observation.portion.updated_datetime" in portion.keys() and portion[
                                "Observation.portion.updated_datetime"]:
                                c = utils.get_component('updated_datetime',
                                                        value=portion["Observation.portion.updated_datetime"],
                                                        component_type='dateTime')
                                portions_observation_components.append(c)

                            portions_observation = None
                            if portions_observation_components:
                                portions_observation = copy.deepcopy(biospecimen_observation)

                                portions_observation['id'] = utils.mint_id(identifier=portion_specimen_identifier,
                                                                           resource_type="Observation",
                                                                           project_id=project_id,
                                                                           namespace=NAMESPACE_GDC)

                                portions_observation['component'] = portions_observation_components

                                portions_observation['subject'] = {"reference": "/".join(["Patient", patient.id])}
                                portions_observation['specimen'] = {
                                    "reference": "/".join(["Specimen", portion_specimen.id])}
                                portions_observation['focus'][0] = {
                                    "reference": "/".join(["Specimen", portion_specimen.id])}

                                if portions_observation not in portion_observations:
                                    portion_observations.append(copy.deepcopy(portions_observation))

                            if "slides" in portion.keys():
                                for slide in portion["slides"]:
                                    portion_img_study = create_imaging_study(slide=slide, patient=patient,
                                                                             sample=portion_specimen)
                                    slide_list.append(portion_img_study)

                                    slides_observation_components = []
                                    if "Observation.slides.section_location" in slide.keys():
                                        c = utils.get_component('section_location',
                                                                value=slide["Observation.slides.section_location"],
                                                                component_type='string')
                                        slides_observation_components.append(c)

                                    slides_observation = None
                                    if slides_observation_components:
                                        slides_observation = copy.deepcopy(biospecimen_imaging_observation)

                                        slides_observation['id'] = utils.mint_id(identifier=Identifier(
                                            **{"system": "".join(["https://gdc.cancer.gov/", "slide_id"]),
                                               "value": slide["ImagingStudy.id"],
                                               "use": "official"}), resource_type="Observation",
                                            project_id=project_id,
                                            namespace=NAMESPACE_GDC)

                                        slides_observation['component'] = slides_observation_components

                                        slides_observation['subject'] = {
                                            "reference": "/".join(["Patient", patient.id])}
                                        slides_observation['specimen'] = {
                                            "reference": "/".join(["Specimen", portion_specimen.id])}
                                        slides_observation['focus'][0] = {
                                            "reference": "/".join(["ImagingStudy", portion_img_study.id])}

                                        if slides_observation not in slides_observations:
                                            slides_observations.append(copy.deepcopy(slides_observation))

                            if "analytes" in portion.keys():
                                for analyte in portion["analytes"]:
                                    if "Specimen.id.analyte" in analyte.keys():
                                        analyte_specimen = Specimen.model_construct()
                                        analyte_specimen.type = specimen.type  # inherits type from initial sample

                                        analyte_specimen_identifier = Identifier(
                                            **{"system": "".join(["https://gdc.cancer.gov/", "analyte_id"]),
                                               "value": analyte["Specimen.id.analyte"],
                                               "use": "official"})
                                        analyte_specimen.id = utils.mint_id(identifier=analyte_specimen_identifier,
                                                                            resource_type="Specimen",
                                                                            project_id=project_id,
                                                                            namespace=NAMESPACE_GDC)

                                        analyte_specimen.identifier = [analyte_specimen_identifier]

                                        analyte_specimen.subject = Reference(
                                            **{"reference": "/".join(["Patient", patient.id])})
                                        analyte_specimen.parent = [
                                            Reference(**{"reference": "/".join(["Specimen", portion_specimen.id])})]

                                        if practitioner_ref:
                                            analyte_specimen.collection = SpecimenCollection(
                                                **{"collector": practitioner_ref})

                                        analyte_specimen.processing = [sp]

                                        if "Specimen.type.analyte" in analyte.keys():
                                            analyte_type = CodeableConcept.model_construct()
                                            analyte_type.coding = [{
                                                'system': "https://cadsr.cancer.gov/experimental_protocol_type",
                                                'display': analyte["Specimen.type.analyte"],
                                                'code': "2513915"}]
                                            analyte_specimen.type = analyte_type

                                        if "slides" in analyte.keys():
                                            for slide in analyte["slides"]:
                                                analyte_img_study = create_imaging_study(slide=slide, patient=patient,
                                                                                         sample=analyte_specimen)
                                                slide_list.append(analyte_img_study)

                                        if not specimen_exists(analyte_specimen.id, all_analytes):
                                            all_analytes.append(analyte_specimen)

                                        analyte_observation_components = []
                                        if "Specimen.type.analyte" in analyte.keys() and analyte[
                                            "Specimen.type.analyte"]:
                                            c = utils.get_component('analyte_type',
                                                                    value=analyte["Specimen.type.analyte"],
                                                                    component_type='string')
                                            analyte_observation_components.append(c)

                                        if "Observation.analyte.concentration" in analyte.keys() and analyte[
                                            "Observation.analyte.concentration"]:
                                            c = utils.get_component('concentration',
                                                                    value=analyte[
                                                                        "Observation.analyte.concentration"],
                                                                    component_type='float')
                                            analyte_observation_components.append(c)

                                        if "Observation.analyte.experimental_protocol_type" in analyte.keys() and \
                                                analyte["Observation.analyte.experimental_protocol_type"]:
                                            c = utils.get_component('experimental_protocol_type',
                                                                    value=analyte[
                                                                        "Observation.analyte.experimental_protocol_type"],
                                                                    component_type='string')
                                            analyte_observation_components.append(c)

                                        if "Observation.analyte.normal_tumor_genotype_snp_match" in analyte.keys() and \
                                                analyte["Observation.analyte.normal_tumor_genotype_snp_match"]:
                                            c = utils.get_component('normal_tumor_genotype_snp_match',
                                                                    value=analyte[
                                                                        "Observation.analyte.normal_tumor_genotype_snp_match"],
                                                                    component_type='string')
                                            analyte_observation_components.append(c)

                                        if "Observation.analyte.ribosomal_rna_28s_16s_ratio" in analyte.keys() and \
                                                analyte["Observation.analyte.ribosomal_rna_28s_16s_ratio"]:
                                            c = utils.get_component('ribosomal_rna_28s_16s_ratio',
                                                                    value=analyte[
                                                                        "Observation.analyte.ribosomal_rna_28s_16s_ratio"],
                                                                    component_type='float')
                                            analyte_observation_components.append(c)

                                        if "Observation.analyte.rna_integrity_number" in analyte.keys() and analyte[
                                            "Observation.analyte.rna_integrity_number"]:
                                            c = utils.get_component('rna_integrity_number',
                                                                    value=analyte[
                                                                        "Observation.analyte.rna_integrity_number"],
                                                                    component_type='float')
                                            analyte_observation_components.append(c)

                                        if "Observation.analyte.spectrophotometer_method" in analyte.keys() and analyte[
                                            "Observation.analyte.spectrophotometer_method"]:
                                            c = utils.get_component('spectrophotometer_method',
                                                                    value=analyte[
                                                                        "Observation.analyte.spectrophotometer_method"],
                                                                    component_type='string')
                                            analyte_observation_components.append(c)

                                        if "Observation.analyte.updated_datetime" in analyte.keys() and analyte[
                                            "Observation.analyte.updated_datetime"]:
                                            c = utils.get_component('updated_datetime',
                                                                    value=analyte[
                                                                        "Observation.analyte.updated_datetime"],
                                                                    component_type='dateTime')
                                            analyte_observation_components.append(c)

                                        if "Specimen.type.sample" in sample.keys() and sample["Specimen.type.sample"]:
                                            c = utils.get_component('sample_type',
                                                                    value=sample["Specimen.type.sample"],
                                                                    component_type='string')
                                            analyte_observation_components.append(c)

                                        analyte_observation = None
                                        if analyte_observation_components:
                                            analyte_observation = copy.deepcopy(biospecimen_observation)
                                            analyte_observation['id'] = utils.mint_id(
                                                identifier=analyte_specimen_identifier,
                                                resource_type="Observation",
                                                project_id=project_id,
                                                namespace=NAMESPACE_GDC)

                                            analyte_observation['component'] = analyte_observation_components

                                            analyte_observation['subject'] = {
                                                "reference": "/".join(["Patient", patient.id])}
                                            analyte_observation['specimen'] = {
                                                "reference": "/".join(["Specimen", analyte_specimen.id])}
                                            analyte_observation['focus'][0] = {
                                                "reference": "/".join(["Specimen", analyte_specimen.id])}

                                            if analyte_observation not in analyte_observations:
                                                analyte_observations.append(copy.deepcopy(analyte_observation))

                                        if "aliquots" in analyte.keys():
                                            for aliquot in analyte["aliquots"]:
                                                if "Specimen.id.aliquot" in aliquot.keys():
                                                    aliquot_specimen = Specimen.model_construct()
                                                    aliquot_specimen.type = specimen.type  # inherits type from initial sample

                                                    aliquot_specimen_identifier = Identifier(
                                                        **{"system": "".join(["https://gdc.cancer.gov/", "aliquot_id"]),
                                                           "value": aliquot["Specimen.id.aliquot"],
                                                           "use": "official"})
                                                    aliquot_specimen.id = utils.mint_id(
                                                        identifier=aliquot_specimen_identifier,
                                                        resource_type="Specimen",
                                                        project_id=project_id,
                                                        namespace=NAMESPACE_GDC)

                                                    aliquot_specimen.identifier = [aliquot_specimen_identifier]

                                                    if practitioner_ref:
                                                        aliquot_specimen.collection = SpecimenCollection(
                                                            **{"collector": practitioner_ref})

                                                    aliquot_specimen.processing = [sp]
                                                    # if aliquot_specimen.id == "3fc2bd45-8cf9-420d-b900-a0fee703731d":
                                                    # print("Patient", patient)

                                                    aliquot_specimen.subject = Reference(
                                                        **{"reference": "/".join(["Patient", patient.id])})
                                                    aliquot_specimen.parent = [Reference(
                                                        **{"reference": "/".join(["Specimen", analyte_specimen.id])})]

                                                    if not specimen_exists(aliquot_specimen.id, all_aliquots):
                                                        all_aliquots.append(aliquot_specimen)

                                                aliquot_observation_components = []
                                                if "Observation.aliquot.analyte_type" in aliquot.keys() and aliquot[
                                                    "Observation.aliquot.analyte_type"]:
                                                    c_aliquot_analyte_type = utils.get_component('aliquot.analyte_type',
                                                                                                 value=aliquot[
                                                                                                     "Observation.aliquot.analyte_type"],
                                                                                                 component_type='string')
                                                    aliquot_observation_components.append(c_aliquot_analyte_type)
                                                if "Observation.aliquot.concentration" in aliquot.keys() and aliquot[
                                                    "Observation.aliquot.concentration"]:
                                                    c = utils.get_component('concentration',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.concentration"],
                                                                            component_type='float')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.aliquot_quantity" in aliquot.keys() and aliquot[
                                                    "Observation.aliquot.aliquot_quantity"]:
                                                    c = utils.get_component('aliquot_quantity',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.aliquot_quantity"],
                                                                            component_type='float')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.aliquot_volume" in aliquot.keys() and aliquot[
                                                    "Observation.aliquot.aliquot_volume"]:
                                                    c = utils.get_component('aliquot_volume',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.aliquot_volume"],
                                                                            component_type='float')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.no_matched_normal_wgs" in aliquot.keys() and isinstance(
                                                        aliquot[
                                                            "Observation.aliquot.no_matched_normal_wgs"], bool):
                                                    c = utils.get_component('no_matched_normal_wgs',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.no_matched_normal_wgs"],
                                                                            component_type='bool')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.no_matched_normal_wxs" in aliquot.keys() and isinstance(
                                                        aliquot[
                                                            "Observation.aliquot.no_matched_normal_wxs"], bool):
                                                    c = utils.get_component('no_matched_normal_wxs',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.no_matched_normal_wxs"],
                                                                            component_type='bool')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.no_matched_normal_low_pass_wgs" in aliquot.keys() and isinstance(
                                                        aliquot[
                                                            "Observation.aliquot.no_matched_normal_low_pass_wgs"],
                                                        bool):
                                                    c = utils.get_component('no_matched_normal_low_pass_wgs',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.no_matched_normal_low_pass_wgs"],
                                                                            component_type='bool')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.no_matched_normal_targeted_sequencing" in aliquot.keys() and isinstance(
                                                        aliquot[
                                                            "Observation.aliquot.no_matched_normal_targeted_sequencing"],
                                                        bool):
                                                    c = utils.get_component('no_matched_normal_targeted_sequencing',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.no_matched_normal_targeted_sequencing"],
                                                                            component_type='bool')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.selected_normal_low_pass_wgs" in aliquot.keys() and isinstance(
                                                        aliquot[
                                                            "Observation.aliquot.selected_normal_low_pass_wgs"], bool):
                                                    c = utils.get_component('selected_normal_low_pass_wgs',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.selected_normal_low_pass_wgs"],
                                                                            component_type='bool')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.selected_normal_targeted_sequencing" in aliquot.keys() and isinstance(
                                                        aliquot[
                                                            "Observation.aliquot.selected_normal_targeted_sequencing"],
                                                        bool):
                                                    c = utils.get_component('selected_normal_targeted_sequencing',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.selected_normal_targeted_sequencing"],
                                                                            component_type='bool')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.selected_normal_wgs" in aliquot.keys() and isinstance(
                                                        aliquot[
                                                            "Observation.aliquot.selected_normal_wgs"], bool):
                                                    c = utils.get_component('selected_normal_wgs',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.selected_normal_wgs"],
                                                                            component_type='bool')
                                                    aliquot_observation_components.append(c)

                                                if "Specimen.type.sample" in sample.keys() and sample[
                                                    "Specimen.type.sample"]:
                                                    c = utils.get_component('sample_type',
                                                                            value=sample["Specimen.type.sample"],
                                                                            component_type='string')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.updated_datetime" in aliquot.keys() and aliquot[
                                                    "Observation.aliquot.updated_datetime"]:
                                                    c = utils.get_component('updated_datetime',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.updated_datetime"],
                                                                            component_type='dateTime')
                                                    aliquot_observation_components.append(c)

                                                if "Observation.aliquot.selected_normal_wxs" in aliquot.keys() and isinstance(
                                                        aliquot[
                                                            "Observation.aliquot.selected_normal_wxs"], bool):
                                                    c = utils.get_component('selected_normal_wxs',
                                                                            value=aliquot[
                                                                                "Observation.aliquot.selected_normal_wxs"],
                                                                            component_type='bool')
                                                    aliquot_observation_components.append(c)

                                                aliquot_observation = None
                                                if aliquot_observation_components:
                                                    aliquot_observation = copy.deepcopy(biospecimen_observation)
                                                    aliquot_observation['id'] = utils.mint_id(
                                                        identifier=aliquot_specimen_identifier,
                                                        resource_type="Observation",
                                                        project_id=project_id,
                                                        namespace=NAMESPACE_GDC)

                                                    aliquot_observation['component'] = aliquot_observation_components

                                                    aliquot_observation['subject'] = {
                                                        "reference": "/".join(["Patient", patient.id])}
                                                    aliquot_observation['specimen'] = {
                                                        "reference": "/".join(["Specimen", aliquot_specimen.id])}
                                                    aliquot_observation['focus'][0] = {
                                                        "reference": "/".join(["Specimen", aliquot_specimen.id])}

                                                    if aliquot_observation not in aliquot_observations:
                                                        aliquot_observations.append(copy.deepcopy(aliquot_observation))

        sample_list = all_samples + all_portions + all_aliquots + all_analytes
        specimen_observations = sample_observations + portion_observations + slides_observations + analyte_observations + aliquot_observations

    def combine_observations(*observation_lists):
        """
        combines multiple lists of observations in a valid FHIR Observation object using model_validate.
        """
        combined = []
        for obs_list in observation_lists:
            for obs in obs_list:
                if isinstance(obs, dict):
                    try:
                        validated_obs = Observation.model_validate(obs)
                        combined.append(validated_obs)
                    except Exception as e:
                        print(f"Failed to validate observation: {obs}, Error: {e}")
                elif isinstance(obs, Observation):
                    combined.append(obs)
                else:
                    print(f"Skipping invalid observation: {type(obs)} -> {obs}")
        return combined

    all_observations = combine_observations(condition_observations, smoking_observation, alcohol_observation,
                                            obs_survey, specimen_observations, staging_observations)
    all_observations = list(
        {obs.id: obs for obs in all_observations if isinstance(obs, Observation) and obs.id}.values())

    for obs in all_observations:
        if not isinstance(obs, Observation):
            print(f"Non-Observation object found: {type(obs)} -> {obs}")

    return {'patient': patient, 'organizations': organizations, "practitioners": practitioners,
            'observations': all_observations, 'condition': condition,
            'research_studies': research_studies, 'research_subject': research_subject, 'specimens': sample_list,
            'imaging_study': slide_list, "procedures": procedures, "med_admin": treatments_medadmin,
            "med": treatments_med, "body_structure": body_structure}


def case_gdc_to_fhir_ndjson(out_dir, name, cases_path, convert, verbose, spinner=None):
    # cases = utils.load_ndjson(cases_path)
    out_path = os.path.join(out_dir, os.pardir, "".join([name, "_keys.ndjson"])) if convert else None
    cases = mapping.convert_maps(in_path=cases_path, out_path=out_path, name=name, convert=convert, verbose=verbose)

    all_fhir_case_obj = []
    [all_fhir_case_obj.append(assign_fhir_for_case(c)) for c in cases]

    def deduplicate_entities(_entities):
        return list({v['id']: v for v in _entities}.values())

    def load_list_entities(_all_fhir_case_obj, _key):
        entity_list = []
        for fhir_case in _all_fhir_case_obj:
            if fhir_case[_key]:
                for entity in fhir_case[_key]:
                    if entity:
                        e = orjson.loads(entity.model_dump_json())
                        entity_list.append(e)
        return deduplicate_entities(entity_list)

    patients = [orjson.loads(fhir_case['patient'].model_dump_json()) for fhir_case in all_fhir_case_obj if
                'patient' in fhir_case.keys() and fhir_case['patient']]
    conditions = deduplicate_entities(
        [orjson.loads(fhir_case['condition'].model_dump_json()) for fhir_case in all_fhir_case_obj if
         'condition' in fhir_case.keys() and fhir_case['condition']])
    research_subjects = deduplicate_entities(
        [orjson.loads(fhir_case['research_subject'].model_dump_json()) for fhir_case in all_fhir_case_obj if
         'research_subject' in fhir_case.keys() and fhir_case['research_subject']])
    body_structure = deduplicate_entities(
        [orjson.loads(fhir_case['body_structure'].model_dump_json()) for fhir_case in all_fhir_case_obj if
         'body_structure' in fhir_case.keys() and fhir_case['body_structure']])
    research_studies = load_list_entities(all_fhir_case_obj, "research_studies")

    specimens = load_list_entities(all_fhir_case_obj, "specimens")
    observations = load_list_entities(all_fhir_case_obj, "observations")
    procedures = load_list_entities(all_fhir_case_obj, "procedures")
    imaging_study = load_list_entities(all_fhir_case_obj, "imaging_study")
    med_admins = load_list_entities(all_fhir_case_obj, "med_admin")
    meds = load_list_entities(all_fhir_case_obj, "med")
    practitioners = load_list_entities(all_fhir_case_obj, "practitioners")
    organizations = load_list_entities(all_fhir_case_obj, "organizations")

    out_dir = out_dir if out_dir.endswith("/") else f"{out_dir}/"

    entity_map = {
        "Specimen": specimens,
        "Patient": patients,
        "Practitioner": practitioners,
        "Organization": organizations,
        "Observation": observations,
        "Condition": conditions,
        "ResearchSubject": research_subjects,
        "ResearchStudy": research_studies,
        "ImagingStudy": imaging_study,
        "Procedure": procedures,
        "BodyStructure": body_structure,
        "MedicationAdministration": med_admins,
        "Medication": meds,
    }

    if spinner:
        spinner.stop()

    for entity_name, entities in entity_map.items():
        if entities:
            cleaned_resource = []
            for resource in entities:
                cleaned_resource_dict = utils.remove_empty_dicts(resource)
                try:
                    validated_resource = utils.validate_fhir_resource_from_type(entity_name,
                                                                                cleaned_resource_dict).model_dump_json()
                except ValueError as e:
                    print(f"Validation failed for {entity_name}: {e}")
                    continue
                # handle pydantic Decimal cases
                validated_resource = utils.convert_decimal_to_float(orjson.loads(validated_resource))
                validated_resource = utils.convert_value_to_float(validated_resource)
                validated_resource = orjson.loads(orjson.dumps(validated_resource).decode("utf-8"))
                cleaned_resource.append(validated_resource)
            if cleaned_resource:
                utils.fhir_ndjson(cleaned_resource, f"{out_dir}{entity_name}.ndjson")
                print(f"Successfully converted GDC case info to FHIR's {entity_name} ndjson file!")


# File ---------------------------------------------------------------
# load file mapped key values
# files = utils.load_ndjson("./tests/fixtures/file/file_key.ndjson")
# file = files[0]

def assign_fhir_for_file(file):
    project_id = "GDC"
    NAMESPACE_GDC = uuid3(NAMESPACE_DNS, 'gdc.cancer.gov')
    group = None

    document = DocumentReference.model_construct()
    document.status = "current"
    data_type = None
    submitter_id = None

    identifiers = []
    assert file['DocumentReference.id'], f"file['DocumentReference.id'] doesn't exist in object:  {file}"
    ident = Identifier(**{"system": "".join(["https://gdc.cancer.gov/", "file_id"]),
                          "value": file['DocumentReference.id'],
                          "use": "official"})

    document.id = utils.mint_id(
        identifier=ident,
        resource_type="DocumentReference",
        project_id=project_id,
        namespace=NAMESPACE_GDC)

    identifiers.append(ident)

    if 'DocumentReference.Identifier' in file.keys() and file['DocumentReference.Identifier']:
        submitter_id = Identifier(**{"system": "".join(["https://gdc.cancer.gov/", "submitter_id"]),
                                     "value": file['DocumentReference.Identifier'],
                                     "use": "secondary"})
        identifiers.append(submitter_id)

    document.identifier = identifiers

    data_category = None
    category = []
    category_keys = {
        "data_category": "data_category",
        "platform": "platform",
        "experimental_strategy": "experimental_strategy",
        "wgs_coverage": "wgs_coverage",
        "data_type": "data_type",
    }
    base_url = "https://gdc.cancer.gov/"

    for key, system_suffix in category_keys.items():
        field = f"DocumentReference.category.{key}"
        if field in file and file[field]:
            cc = CodeableConcept.model_construct()
            cc.coding = [{
                "system": "".join([base_url, system_suffix]),
                "display": file[field],
                "code": str(file[field])
            }]
            category.append(cc)
            if key == "data_category":
                data_category = file[field]

    if category:
        document.category = category

    if 'DocumentReference.version' in file.keys() and file['DocumentReference.version']:
        document.version = file['DocumentReference.version']

    if 'DocumentReference.date' in file.keys() and file['DocumentReference.date']:
        document.date = file['DocumentReference.date']

    patients = []
    sample_ref = []
    # print(f"Data Category: {data_category}\n")
    if 'cases' in file.keys() and file['cases']:
        for case in file['cases']:
            patient_id_identifier = Identifier.model_construct()
            patient_id_identifier.value = case['Patient.id']
            patient_id_identifier.use = "official"
            patient_id_identifier.system = "".join(["https://gdc.cancer.gov/", "case_id"])

            patient_id = utils.mint_id(identifier=patient_id_identifier, resource_type="Patient", project_id=project_id,
                                       namespace=NAMESPACE_GDC)

            patients.append(Reference(**{"reference": "/".join(["Patient", patient_id])}))

            if 'samples' in case.keys():
                for sample in case['samples']:
                    if 'portions' in sample.keys() and 'Specimen.id.aliquots' in \
                            sample['portions'][0]['analytes'][0]['aliquots'][0].keys() and \
                            sample['portions'][0]['analytes'][0]['aliquots'][0]['Specimen.id.aliquots']:
                        specimen_identifier = Identifier(
                            **{"system": "".join(["https://gdc.cancer.gov/", "aliquot_id"]),
                               "value": sample['portions'][0]['analytes'][0]['aliquots'][0]['Specimen.id.aliquots']})

                        specimen_id = utils.mint_id(identifier=specimen_identifier, resource_type="Specimen",
                                                    project_id=project_id,
                                                    namespace=NAMESPACE_GDC)

                        sample_ref.append(Reference(**{"reference": "/".join(["Specimen", specimen_id])}))

                    elif data_category in ['Clinical', 'Biospecimen'] and 'Specimen.id.samples' in sample.keys() and \
                            sample['Specimen.id.samples']:
                        # print(sample['Specimen.id.samples'], document.category, "\n")
                        specimen_identifier = Identifier(
                            **{"system": "".join(["https://gdc.cancer.gov/", "sample_id"]),
                               "value": sample['Specimen.id.samples']})

                        specimen_id = utils.mint_id(identifier=specimen_identifier, resource_type="Specimen",
                                                    project_id=project_id,
                                                    namespace=NAMESPACE_GDC)

                        sample_ref.append(Reference(**{"reference": "/".join(["Specimen", specimen_id])}))

    # keeping code incase - patient comes back on DocumentReference
    doc_subject_reference = []
    patient_group = None
    if patients and len(patients) == 1:
        doc_subject_reference.append(patients[0])
    else:
        patient_members = [GroupMember(**{'entity': p}) for p in patients]
        patient_reference_ids = [p.reference for p in patients]
        patient_group_identifier = Identifier(
            **{"system": "".join(["https://gdc.cancer.gov/", "patient_group"]),
               "value": "/".join(patient_reference_ids + [document.identifier[0].value]),
               "use": "official"})

        patient_group_id = utils.mint_id(identifier=patient_group_identifier, resource_type="Group",
                                         project_id=project_id,
                                         namespace=NAMESPACE_GDC)

        patient_group = Group(
            **{'id': patient_group_id, "identifier": [patient_group_identifier], "membership": 'definitional',
               'member': patient_members, "type": "person"})
        doc_subject_reference.append(Reference(**{"reference": "/".join(["Group", patient_group.id])}))
        # document.subject = Reference(**{"reference": "/".join(["Group", patient_group.id])})

    if sample_ref and len(sample_ref) == 1:
        document.subject = sample_ref[0]
    else:
        specimen_members = [GroupMember(**{'entity': s}) for s in sample_ref]
        reference_ids = [s.reference for s in sample_ref]
        group_identifier = Identifier(
            **{"system": "".join(["https://gdc.cancer.gov/", "sample_group"]),
               "value": "/".join(reference_ids + ["Documentreference/" + document.identifier[0].value]),
               "use": "official"})

        group_id = utils.mint_id(identifier=group_identifier, resource_type="Group",
                                 project_id=project_id,
                                 namespace=NAMESPACE_GDC)
        if specimen_members:
            group = Group(**{'id': group_id, "identifier": [group_identifier], "membership": 'definitional',
                             'member': specimen_members, "type": "specimen"})

            document.subject = Reference(**{"reference": "/".join(["Group", group.id])})

    # TODO: temporary fix for document.subject reference
    # missing in initial script - should have data downloaded for portion UUID, Slide UUID, and associated sample UUID
    if not document.subject:
        if patients and len(patients) == 1:
            document.subject = patients[0]
        elif patient_group:
            group = patient_group
            document.subject = Reference(**{"reference": "/".join(["Group", patient_group.id])})

    if not document.subject:
        with open("no_reference.log", "a") as log_file:
            log_file.write(
                f"No subject found for file id: {file['DocumentReference.id']}, Data Type {data_type}\n")

    attachment = Attachment.model_construct()
    attachment.url = "https://api.gdc.cancer.gov/data/{}".format(file['DocumentReference.id'])

    if 'Attachment.title' in file.keys() and file['Attachment.title']:
        attachment.title = file['Attachment.title']
    if 'Attachment.hash' in file.keys() and file['Attachment.hash']:
        attachment.hash = file['Attachment.hash']
    if 'Attachment.size' in file.keys() and file['Attachment.size']:
        attachment.size = file['Attachment.size']

    profile = None
    if 'DocumentReference.content.profile' in file.keys() and file['DocumentReference.content.profile']:
        profile = DocumentReferenceContentProfile.model_construct()
        system = "".join(["https://gdc.cancer.gov/", "data_format"])
        profile.valueCoding = {"code": file['DocumentReference.content.profile'],
                               "display": file['DocumentReference.content.profile'],
                               "system": system}

        cc_type = CodeableConcept.model_construct()
        system = "".join(["https://gdc.cancer.gov/", "data_format"])
        cc_type.coding = [{'system': system,
                           'display': file['DocumentReference.content.profile'],
                           'code': file['DocumentReference.content.profile']}]

        document.type = cc_type

        attachment.contentType = file['DocumentReference.content.profile']

    if profile:
        data = {'attachment': attachment, "profile": [profile]}
    else:
        data = {'attachment': attachment}
    document.content = [DocumentReferenceContent(**data)]

    docref_observations = []
    if 'read_groups' in file.keys() and file['read_groups']:
        docref_observation = copy.deepcopy(file_observation)
        for observation in file['read_groups']:
            observation_identifier = Identifier(
                **{"system": "".join(["https://gdc.cancer.gov/", "files.analysis.metadata.read_groups"]),
                   "value": observation['Observation.DocumentReference.read_group_id'],
                   "use": "official"})
            docref_observation['id'] = utils.mint_id(identifier=observation_identifier,
                                                     resource_type="Observation",
                                                     project_id=project_id,
                                                     namespace=NAMESPACE_GDC)

            identifiers = []
            if 'Observation.DocumentReference.submitter_id' in observation.keys() and observation[
                'Observation.DocumentReference.submitter_id']:
                read_groups_submitter_id = Identifier(
                    **{"system": "".join(
                        ["https://gdc.cancer.gov/", "files.analysis.metadata.read_groups.submitter_id"]),
                        "value": observation['Observation.DocumentReference.submitter_id'],
                        "use": "official"})
                identifiers.append(orjson.loads(read_groups_submitter_id.model_dump_json()))

            identifiers.append(orjson.loads(observation_identifier.model_dump_json()))
            docref_observation['identifier'] = identifiers
            docref_observation['focus'] = [
                orjson.loads(
                    Reference(**{"reference": "/".join(["DocumentReference", document.id])}).model_dump_json())]
            docref_observation['subject'] = orjson.loads(doc_subject_reference[0].model_dump_json())
            obs_components = []
            obs_component_fields = {
                "adapter_name": "string",
                "adapter_sequence": "string",
                "base_caller_name": "string",
                "base_caller_version": "string",
                "created_datetime": "string",
                "experiment_name": "string",
                "flow_cell_barcode": "string",
                "includes_spike_ins": "string",
                "instrument_model": "string",
                "is_paired_end": "bool",
                "library_name": "string",
                "library_preparation_kit_catalog_number": "string",
                "library_preparation_kit_name": "string",
                "library_preparation_kit_vendor": "string",
                "library_preparation_kit_version": "string",
                "library_selection": "string",
                "library_strand": "string",
                "library_strategy": "string",
                "platform": "string",
                "read_group_id": "string",
                "read_group_name": "string",
                "read_length": "float",
                "RIN": "float",
                "sequencing_center": "string",
                "sequencing_date": "string",
                "size_selection_range": "string",
                "spike_ins_concentration": "string",
                "spike_ins_fasta": "string",
                "state": "string",
                "target_capture_kit": "string",
                "target_capture_kit_catalog_number": "string",
                "target_capture_kit_name": "string",
                "target_capture_kit_target_region": "string",
                "target_capture_kit_vendor": "string",
                "target_capture_kit_version": "string",
                "to_trim_adapter_sequence": "bool",
                "updated_datetime": "string",
                "days_to_sequencing": "int",
                "single_cell_library": "string",
                "multiplex_barcode": "string",
                "fragment_standard_deviation_length": "float",
                "fragment_mean_length": "float",
                "fragment_minimum_length": "int",
                "fragment_maximum_length": "float",
                "lane_number": "int",
                "number_expect_cells": "int"
            }
            base_system = "https://cadsr.cancer.gov/files.analysis.metadata.read_groups"
            for key, comp_type in obs_component_fields.items():
                field_key = f"Observation.DocumentReference.{key}"
                if field_key in observation.keys() and observation[field_key]:
                    obs_component = utils.get_component(
                        key=key,
                        value=observation[field_key],
                        component_type=comp_type,
                        system=base_system
                    )
                    if obs_component:
                        obs_components.append(obs_component)

            if obs_components:
                docref_observation['component'] = obs_components

            docref_observations.append(docref_observation)

    return {'files': document, 'observations': docref_observations, 'group': group}


def file_gdc_to_fhir_ndjson(out_dir, name, files_path, convert, verbose, spinner=None):
    #  files = utils.load_ndjson(files_path)
    out_path = os.path.join(out_dir, os.pardir, "".join([name, "_keys.ndjson"])) if convert else None
    files = mapping.convert_maps(in_path=files_path, out_path=out_path, name=name, convert=convert, verbose=verbose)

    all_fhir_file_obs_obj = []
    all_fhir_file_obj = []
    all_groups = []
    for file in files:
        obj = assign_fhir_for_file(file)
        if obj['files']:
            all_fhir_file_obj.append(obj['files'])
        if obj['observations']:
            all_fhir_file_obs_obj.append(obj['observations'])
        if obj['group']:
            all_groups.append(obj['group'])

    doc_refs = [orjson.loads(fhir_file.model_dump_json()) for fhir_file in all_fhir_file_obj]
    groups = [orjson.loads(group.json()) for group in all_groups]

    observations_list = []
    for observations in all_fhir_file_obs_obj:
        if observations:
            for obs in observations:
                if isinstance(obs, dict):
                    observations_list.append(obs)
    observations_list = list({v['id']: v for v in observations_list}.values())

    if spinner:
        spinner.stop()

    if observations_list:
        utils.create_or_extend(new_items=observations_list, folder_path=out_dir, resource_type='Observation',
                               update_existing=False)

    if "/" not in out_dir[-1]:
        out_dir = out_dir + "/"

    if doc_refs:
        cleaned_doc_refs = utils.clean_resources(doc_refs)
        if cleaned_doc_refs:
            utils.fhir_ndjson(cleaned_doc_refs, "".join([out_dir, "DocumentReference.ndjson"]))
            print("Successfully converted GDC file info to FHIR's DocumentReference ndjson file!")

    if groups:
        cleaned_groups = utils.clean_resources(groups)
        if cleaned_groups:
            utils.fhir_ndjson(groups, "".join([out_dir, "Group.ndjson"]))
            print("Successfully converted GDC file's patients info to FHIR's Group ndjson file!")


# Cellosaurus ---------------------------------------------------------------

def cellosaurus_resource(path, out_dir):
    out_dir = os.path.abspath(out_dir)
    out_dir = os.path.join(out_dir, "")

    ids = utils.cellosaurus_cancer_ids(path, os.path.join(out_dir, "ids.json"), save=True)  # filter step
    if ids:
        print("Successfully saved cellosaurus ids!")
    else:
        print("There aren't any cancer human cell-lines with sex annotation and depmap reference.")
        return

    cells_dir = os.path.join(out_dir, "cells")
    if not os.path.exists(cells_dir):
        os.makedirs(cells_dir)
    cells_dir = os.path.abspath(cells_dir)
    cells_dir = os.path.join(cells_dir, "")

    utils.fetch_cellines(ids, cells_dir)  # api call intensive - 1s per request + 0.5s delay
    cls = utils.cellosaurus_cancer_jsons(cells_dir)
    ndjson_path = os.path.join(out_dir, "cellosaurus_cellines.ndjson")
    utils.fhir_ndjson(cls, os.path.join(out_dir, "cellosaurus_cellines.ndjson"))

    if os.path.exists(ndjson_path):
        print("Successfully saved cell lines in cellosaurus_cellines.ndjson!")


def cellosaurus_fhir_mappping(cell_lines, verbose=False):
    project_id = "CELLOSAURUS"
    NAMESPACE_CELLOSAURUS = uuid3(NAMESPACE_DNS, 'cellosaurus.org')

    patients = []
    conditions = []
    samples = []

    for cell_line in cell_lines:
        for cl in cell_line["Cellosaurus"]["cell-line-list"]:
            patient = None
            patient_id = None
            ident_list = []
            for accession in cl["accession-list"]:
                if accession["type"] == "primary":
                    patient_identifier = Identifier(
                        **{"system": "https://www.cellosaurus.org/cell-line-primary-accession",
                           "value": accession["value"],
                           "use": "official"})
                    patient_id = utils.mint_id(identifier=patient_identifier, resource_type="Patient",
                                               project_id=project_id,
                                               namespace=NAMESPACE_CELLOSAURUS)

                    ident_list.append(patient_identifier)
            if patient_id:
                for identifier in cl["name-list"]:
                    if identifier["type"] == "identifier":
                        patient_identifer = identifier["value"]
                        ident_identifier = Identifier.model_construct()
                        ident_identifier.value = patient_identifer
                        ident_identifier.system = "https://www.cellosaurus.org/name-list"
                        ident_identifier.use = "secondary"
                        ident_list.append(ident_identifier)

                for xref in cl["xref-list"]:
                    if xref["database"] == "DepMap":
                        depmap_identifier = Identifier.model_construct()
                        depmap_identifier.value = xref["accession"]
                        # dep_map_url = xref["url"] # ex. https://depmap.org/portal/cell_line/ACH-000035"
                        depmap_identifier.system = "https://depmap.org/cell_line"
                        depmap_identifier.use = "secondary"
                        ident_list.append(depmap_identifier)

                    if xref["database"] == "Cosmic":
                        cosmic_identifier = Identifier.model_construct()
                        cosmic_identifier.value = xref["accession"]
                        cosmic_identifier.system = "https://cancer.sanger.ac.uk/cosmic/cell_line"
                        cosmic_identifier.use = "secondary"
                        ident_list.append(cosmic_identifier)

                if "sex" in cl.keys() and cl["sex"]:
                    gender = cl["sex"].lower()
                    patient = Patient(
                        **{"id": patient_id, "gender": gender, "identifier": ident_list})
                    patients.append(patient)
                    patient_ref = Reference(**{"reference": "/".join(["Patient", patient_id])})

                if patient:
                    # add condition from disease-list
                    if "disease-list" in cl.keys():
                        for disease_annotation in cl["disease-list"]:
                            condition_identifier = Identifier(
                                **{"system": "https://www.cellosaurus.org/disease",
                                   "value": disease_annotation["accession"],
                                   "use": "official"})
                            condition_id = utils.mint_id(identifier=condition_identifier, resource_type="Condition",
                                                         project_id=project_id,
                                                         namespace=NAMESPACE_CELLOSAURUS)

                            if "terminology" in disease_annotation.keys() and disease_annotation[
                                "terminology"] == "NCIt":
                                condition_clinicalstatus_code = CodeableConcept.model_construct()
                                condition_clinicalstatus_code.coding = [
                                    {"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                     "display": "unknown", "code": "unknown"}]

                                disease_coding = []
                                code = disease_annotation["accession"]

                                if "value" in disease_annotation.keys():
                                    display = disease_annotation["value"]
                                elif "label" in disease_annotation.keys():
                                    display = disease_annotation["label"]
                                else:
                                    display = "place_holder"

                                coding = {'system': "https://ncit.nci.nih.gov/", 'display': display, 'code': code}

                                disease_coding.append(coding)

                                mondo = [d["mondo_id"] for d in ncit2mondo if
                                         d["ncit_id"] == disease_annotation["accession"]]
                                if mondo:
                                    mondo_code = str(mondo[0])
                                    mondo_display = display
                                    mondo_coding = {'system': "https://www.ebi.ac.uk/ols4/ontologies/mondo",
                                                    'display': mondo_display, 'code': mondo_code}
                                    disease_coding.append(mondo_coding)

                                cc = CodeableConcept.model_construct()
                                cc.coding = disease_coding

                                onset_age = None
                                if "age" in cl.keys() and cl["age"]:
                                    if "Y" not in cl["age"] and cl["age"][-1] == "M":
                                        age = round(int(cl["age"].split("M")[0]) / 12, 2)
                                        onset_age = Age(**{"value": age})
                                    elif "Y" in cl["age"]:
                                        age = cl["age"].split("Y")[0]
                                        if "-" in age:
                                            age = age.split("-")[0]
                                        if age.startswith(">"):
                                            age = age.replace(">", "")

                                        # onset_age = Age(**{"value": age})

                                        patient.extension = [{
                                            "url": "http://hl7.org/fhir/SearchParameter/patient-extensions-Patient-age",
                                            "valueQuantity": {
                                                "value": age
                                            }
                                        }]

                                    else:
                                        if verbose:
                                            print("Age syntax doesn't match: ", cl["age"])

                                if onset_age:
                                    conditions.append(Condition(
                                        **{"id": condition_id, "identifier": [condition_identifier], "code": cc,
                                           "subject": patient_ref,
                                           "clinicalStatus": condition_clinicalstatus_code, "onsetAge": onset_age}))
                                else:
                                    conditions.append(Condition(
                                        **{"id": condition_id, "identifier": [condition_identifier], "code": cc,
                                           "subject": patient_ref,
                                           "clinicalStatus": condition_clinicalstatus_code}))

                    sample_parents_ref = []
                    # sample hierarchy
                    if "derived-from" in cl.keys() and cl["derived-from"]:
                        for parent_cell in cl["derived-from"]:
                            if "terminology" in parent_cell.keys() and parent_cell["terminology"] == "Cellosaurus":

                                parent_identifier = Identifier(
                                    **{"system": "https://www.cellosaurus.org/cell-line-primary-accession",
                                       "value": "/".join(["Specimen", parent_cell["accession"]]),
                                       "use": "official"})
                                parent_id = utils.mint_id(identifier=parent_identifier, resource_type="Specimen",
                                                          project_id=project_id,
                                                          namespace=NAMESPACE_CELLOSAURUS)

                                parent_id_identifier = Identifier.model_construct()
                                parent_id_identifier.value = "/".join(["Specimen", parent_cell["accession"]])
                                parent_id_identifier.system = "https://www.cellosaurus.org/"

                                parent_identifier = Identifier.model_construct()
                                parent_identifier.value = "/".join(["Specimen", parent_cell["value"]])
                                parent_identifier.system = "https://www.cellosaurus.org/"
                                parent_identifier.use = "official"

                                parent_sample = Specimen(
                                    **{"id": parent_id, "identifier": [parent_id_identifier, parent_identifier]})
                                if parent_sample not in samples:
                                    samples.append(parent_sample)
                                sample_parents_ref.append(Reference(**{"reference": "/".join(["Specimen", parent_id])}))

                    specimen_identifier = Identifier(
                        **{"system": "https://www.cellosaurus.org/cell-line-primary-accession",
                           "value": "/".join(["Specimen", patient_identifier.value]),
                           "use": "official"})
                    specimen_id = utils.mint_id(identifier=specimen_identifier, resource_type="Specimen",
                                                project_id=project_id,
                                                namespace=NAMESPACE_CELLOSAURUS)

                    if sample_parents_ref:
                        samples.append(Specimen(
                            **{"id": specimen_id, "subject": patient_ref, "identifier": [specimen_identifier],
                               "parent": sample_parents_ref}))
                    else:
                        samples.append(Specimen(
                            **{"id": specimen_id, "subject": patient_ref, "identifier": [specimen_identifier]}))

    return {"patients": patients, "conditions": conditions, "samples": samples}


def cellosaurus_to_fhir_ndjson(out_dir, obj, spinner):
    patients = [orjson.loads(patient.json()) for patient in obj["patients"]]
    samples = [orjson.loads(sample.json()) for sample in obj["samples"]]
    samples = list({v['id']: v for v in samples}.values())
    conditions = [orjson.loads(condition.json()) for condition in obj["conditions"]]
    conditions = list({v['id']: v for v in conditions}.values())

    if spinner:
        spinner.stop()

    if patients:
        cleaned_patients = utils.clean_resources(patients)
        utils.fhir_ndjson(cleaned_patients, os.path.join(out_dir, "Patient.ndjson"))
        print("Successfully converted Cellosaurus info to FHIR's Patient ndjson file!")
    if samples:
        cleaned_samples = utils.clean_resources(samples)
        utils.fhir_ndjson(cleaned_samples, os.path.join(out_dir, "Specimen.ndjson"))
        print("Successfully converted Cellosaurus info to FHIR's Specimen ndjson file!")
    if conditions:
        cleaned_conditions = utils.clean_resources(conditions)
        utils.fhir_ndjson(cleaned_conditions, os.path.join(out_dir, "Condition.ndjson"))
        print("Successfully converted Cellosaurus info to FHIR's Condition ndjson file!")


def cellosaurus2fhir(path, out_dir, spinner=None):
    cell_lines = utils.load_ndjson(path=path)
    cellosaurus_fhir_objects = cellosaurus_fhir_mappping(cell_lines)
    cellosaurus_to_fhir_ndjson(out_dir=out_dir, obj=cellosaurus_fhir_objects, spinner=spinner)
