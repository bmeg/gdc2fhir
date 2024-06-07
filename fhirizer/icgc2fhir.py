import os
import re
import glob
import pathlib
import inflection
import pandas as pd
import uuid
import json
import orjson
import copy
from fhir.resources.identifier import Identifier
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.encounter import Encounter
from fhir.resources.extension import Extension
from fhir.resources.reference import Reference
from fhir.resources.condition import Condition, ConditionStage
from fhir.resources.observation import Observation
from fhir.resources.specimen import Specimen, SpecimenProcessing, SpecimenCollection
from fhir.resources.patient import Patient
from fhir.resources.researchsubject import ResearchSubject
from fhir.resources.procedure import Procedure
from fhir.resources.medicationadministration import MedicationAdministration
from fhir.resources.bodystructure import BodyStructure, BodyStructureIncludedStructure
from fhir.resources.medication import Medication
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.documentreference import DocumentReference, DocumentReferenceContent, \
    DocumentReferenceContentProfile
from fhir.resources.attachment import Attachment
from fhir.resources.age import Age
from fhirizer import utils
from datetime import datetime
import importlib.resources
from pathlib import Path

# smoking_obs = utils._read_json(str(Path(importlib.resources.files(
#    'fhirizer').parent / 'resources' / 'icgc' / 'observations' / 'smoking.json')))
# alcohol_obs = utils._read_json(str(Path(importlib.resources.files(
#    'fhirizer').parent / 'resources' / 'icgc' / 'observations' / 'alcohol.json')))

smoking_obs = utils._read_json("resources/icgc/observations/smoking.json")
alcohol_obs = utils._read_json("resources/icgc/observations/alcohol.json")

project_name = ""

this_project_path = "../ICGC/"
map_path = f"./projects/ICGC/{project_name}/*.xlsx"
dat_path = f"./projects/ICGC/{project_name}/*.csv"
out_path = f"./projects/ICGC/{project_name}"

conditionoccurredFollowing = {
    "extension": [
        {
            "url": "https://dcc.icgc.org",
            "valueCoding": {
                "system": "http://snomed.info/sct",
                "code": "",
                "display": ""
            }
        }
    ],
    "url": "http://hl7.org/fhir/StructureDefinition/condition-occurredFollowing",
    "valueString": ""
},

conditionoccurredFollowing_snomed_code = {"disease progression": "246450006", "stable disease": "58158008",
                                          "unknown": "261665006", "partial response": "399204005"}

# ResearchStudy condition codes
SC = [{
    "system": "http://snomed.info/sct",
    "code": "118286007",
    "display": "Squamous Cell Neoplasms"
},
    {
        "system": "http://snomed.info/sct",
        "code": "115215004",
        "display": "Adenomas and Adenocarcinomas"
    }]

ES = [{
    "system": "http://snomed.info/sct",
    "code": "276803003",
    "display": "Adenocarcinoma of esophagus"},
    {
        "system": "http://snomed.info/sct",
        "code": "115215004",
        "display": "Adenomas and Adenocarcinomas"
    }]

relapse_type_snomed = {"Local recurrence of malignant tumor of esophagus": "314960002",
                       "Distant metastasis present": "399409002"}

smoking_snomed_codes = [
    {
        "snomed_code": "77176002",
        "snomed_display": "Current smoker",
        "text": "Current smoker",
        "note_text": "Current smoker"
    },
    {
        "snomed_code": "8392000",
        "snomed_display": "Non-smoker",
        "text": "Non-smoker",
        "note_text": "Lifelong non-smoker (<100 cigarettes smoked in lifetime)"
    }
]

alcohol_snomed_codes = [
    {
        "snomed_code": "228276006",
        "snomed_display": "Occasional drinker",
        "text": "Occasional drinker",
        "note_text": "Occasional Drinker (< once a month)"
    },
    {
        "snomed_code": "28127009",
        "snomed_display": "Social drinker",
        "text": "Social drinker",
        "note_text": "Social Drinker (> once a month, < once a week)"
    },
    {
        "snomed_code": "225769003",
        "snomed_display": "Once a week",
        "text": "Once a week",
        "note_text": "Weekly Drinker (>=1x a week)"
    },
    {
        "snomed_code": "69620002",
        "snomed_display": "Daily",
        "text": "Daily",
        "note_text": "Daily Drinker"
    }
]

exam = {
    "resourceType": "Observation",
    "id": "f026c5e8-d485-593f-af5c-38080d0ea4f9",
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "exam",
                    "display": "exam"
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "https://terminology.hl7.org/5.1.0/NamingSystem-icd10CM.html",
                "code": "C34.1",
                "display": "Malignant neoplasm of upper lobe, bronchus or lung"
            }
        ]
    }
}

dictionary_cols = ['csv_column_name',
                   'csv_description',
                   'csv_type',
                   'csv_type_notes',
                   'fhir_resource_type',
                   'coding_system',
                   'coding_code',
                   'coding_display',
                   'coding_version',
                   'observation_subject',
                   'uom_system',
                   'uom_code',
                   'uom_unit']


def project_files(path, project):
    dir_path = "".join([path, project, "/*.tsv.gz"])
    all_paths = glob.glob(dir_path)
    return all_paths


def fetch_paths(path):
    all_paths = glob.glob(path)
    return all_paths


def get_df(file_path):
    df = pd.read_csv(file_path, compression='gzip', sep="\t")
    df = df.fillna('')
    return df


def simplify_data_types(data_type):
    if data_type in ['int64', 'int32', 'int16']:
        return 'integer'
    elif data_type in ['float64', 'float32', 'float16']:
        return 'float'
    elif data_type in ['object', 'string']:
        return 'string'
    elif data_type == 'bool':
        return 'boolean'
    elif data_type in ['datetime64[ns]', 'timedelta64[ns]', 'period']:
        return 'date'
    else:
        print(f"New Data type: {data_type}.")
        return data_type


def reform(df, out_path, project_name=None, df_type=None, file_name="data-dictionary-original"):
    df.columns = df.columns.to_series().apply(lambda x: inflection.underscore(inflection.parameterize(x)))

    data_type_list = []
    [data_type_list.append(simplify_data_types(str(pd_dat_type.name))) for pd_dat_type in list(df.dtypes)]

    df_dictionary = pd.DataFrame(columns=dictionary_cols)
    df_dictionary['csv_column_name'] = list(df.columns)

    df_dictionary['csv_type'] = data_type_list
    df_dictionary = df_dictionary.fillna('')

    if project_name:
        file_name = "-".join([df_type, project_name, file_name])

    df_dictionary.to_excel(pathlib.Path(out_path) / f"{file_name}.xlsx", index=False)
    df.to_csv(pathlib.Path(out_path) / f"{file_name}.csv", index=False)


def init_mappings(paths, out_path):
    # caution this re-writes mappings
    for path in paths:
        if "donor_therapy" in path:
            donor_therapy_df = get_df(path)
            reform(donor_therapy_df, out_path, project_name=project_name, df_type="donor_therapy",
                   file_name="data-dictionary-original")
        elif "donor_exposure" in path:
            donor_exposure_df = get_df(path)
            reform(donor_exposure_df, out_path, project_name=project_name, df_type="donor_exposure",
                   file_name="data-dictionary-original")
        elif "donor_surgery" in path:
            donor_surgery_df = get_df(path)
            reform(donor_surgery_df, out_path, project_name=project_name, df_type="donor_surgery",
                   file_name="data-dictionary-original")
        elif "donor_family" in path:
            donor_family_df = get_df(path)
            reform(donor_family_df, out_path, project_name=project_name, df_type="donor_family",
                   file_name="data-dictionary-original")
        elif "donor." in path:
            donor_df = get_df(path)
            reform(donor_df, out_path, project_name=project_name, df_type="donor",
                   file_name="data-dictionary-original")
        elif "sample" in path:
            sample_df = get_df(path)
            reform(sample_df, out_path, project_name=project_name, df_type="sample",
                   file_name="data-dictionary-original")
        elif "specimen" in path:
            specimen_df = get_df(path)
            reform(specimen_df, out_path, project_name=project_name, df_type="specimen",
                   file_name="data-dictionary-original")
        elif "simple_somatic_mutation.open" in path:
            ssm_df = get_df(path)
            reform(ssm_df, out_path, project_name=project_name, df_type="simple_somatic_mutation",
                   file_name="data-dictionary-original")
        # elif "copy_number_somatic_mutation" in path:
        #    cnsm_df = get_df(path)
        #    reform(cnsm_df, out_path, project_name=project_name, df_type="copy_number_somatic_mutation",
        #           file_name="data-dictionary-original")


def fetch_mappings(file_paths, project_name='ESAD-UK'):
    df_dict = {}
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        key = file_name.split("-" + project_name)[0]

        df = pd.read_excel(file_path)
        df_subset = df[['csv_column_name', 'csv_type', 'fhir_resource_type']]
        df_subset = df_subset.fillna('')
        df_dict[key] = df_subset
    return df_dict


def fetch_data(file_paths, project_name):
    df_dict = {}
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        key = file_name.split("-" + project_name)[0]

        df = pd.read_csv(file_path)
        df = df.fillna('')
        df_dict[key] = df
    return df_dict


paths = project_files(path=this_project_path, project=project_name)
# init_mappings(paths, out_path)

mp = fetch_paths(map_path)
mp_dict = fetch_mappings(mp)

dat_paths = fetch_paths(dat_path)
dat_paths = [path for path in dat_paths if
             "simple_somatic_mutation" not in path and "copy_number_somatic_mutation" not in path]

dat_dict = fetch_data(dat_paths, project_name=project_name)

# combine sample and specimen relations
df_specimen = pd.merge(dat_dict['specimen'], dat_dict['sample'], on='icgc_specimen_id', how='left',
                     suffixes=('_specimen', '_sample'))

# combine patient and exposure observations
# https://loinc.org/LG41856-2
if 'donor_exposure' in dat_dict.keys():
    df_patient = pd.merge(dat_dict['donor'], dat_dict['donor_exposure'], on='icgc_donor_id', how='left',
                          suffixes=('', '_donor_exposure'))
    df_patient.fillna('')
else:
    df_patient = dat_dict['donor']


# TODO: family cancer history observation link confirmation
# df_patient_exposure_family = pd.merge(dat_dict['donor'], dat_dict['donor_family'], on='icgc_donor_id', how='left',
#                        suffixes=('', '_donor_family'))
# df_patient_exposure_family = df_patient_exposure_family.fillna('')


def fhir_research_study(df=dat_dict['donor']):
    name = df["project_code"].unique()[0]

    rs_name = "icgc_project"
    condition = None
    if name in ["ESAD-UK", "ESCA-CN"]:
        rs_name = "Esophageal Adenocarcinoma"
        condition = CodeableConcept(**{"coding": ES})
    elif name in ["LUSC-KR", "LUSC-CN"]:
        rs_name = "Lung Squamous cell carcinoma"
        condition = CodeableConcept(**{"coding": SC})

    research_study_list = []
    icgc_program = ResearchStudy(**{"id": str(uuid.uuid3(uuid.NAMESPACE_DNS, "ICGC")),
                                    "identifier": [
                                        Identifier(**{"system": "https://dcc.icgc.org/program", "value": "ICGC"})],
                                    "name": "ICGC", "status": "active"})
    research_study_list.append(icgc_program)

    icgc_project = ResearchStudy(**{"id": str(uuid.uuid3(uuid.NAMESPACE_DNS, name)),
                                    "identifier": [
                                        Identifier(**{"system": "https://dcc.icgc.org/project", "value": name})],
                                    "name": rs_name, "status": "active", "partOf": [
            Reference(**{"reference": "/".join(["ResearchStudy", icgc_program.id])})],
                                    "condition": [condition]})
    research_study_list.append(icgc_project)

    studies = [value for value in df['study_donor_involved_in'].unique() if value]

    if studies:
        for study in studies:
            icgc_study = ResearchStudy(**{"id": str(uuid.uuid3(uuid.NAMESPACE_DNS, study)),
                                          "identifier": [
                                              Identifier(**{"system": "https://dcc.icgc.org/study", "value": study})],
                                          "name": rs_name, "status": "active", "partOf": [
                    Reference(**{"reference": "/".join(["ResearchStudy", icgc_program.id])}),
                    Reference(**{"reference": "/".join(["ResearchStudy", icgc_project.id])})]})
            research_study_list.append(icgc_study)
    return research_study_list


# row = dat_dict['donor'].iloc[0]

def exposure_observation(obs, row, snomed, smoking):
    patient_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join([row['icgc_donor_id'], row['project_code']])))
    if smoking:
        obs["note"][0]["text"] = row['tobacco_smoking_history_indicator']
    else:
        obs["note"][0]["text"] = row['alcohol_history_intensity']
    obs["subject"] = {"reference": "".join(["Patient/", patient_id])}
    obs["focus"] = [{"reference": "".join(["Patient/", patient_id])}]
    obs["id"] = str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join([patient_id, row['project_code'], obs["note"][0]["text"]])))

    if snomed:
        obs["valueCodeableConcept"]["coding"][0]["code"] = snomed["snomed_code"]
        obs["valueCodeableConcept"]["coding"][0]["display"] = snomed["snomed_display"]
        obs["valueCodeableConcept"]["text"] = snomed["text"]
    return obs


def fhir_smoking_exposure_observations(row):
    obs = None
    if 'tobacco_smoking_history_indicator' in row.keys() and pd.notna(
            row['tobacco_smoking_history_indicator']) and isinstance(row['tobacco_smoking_history_indicator'], str):
        if row['tobacco_smoking_history_indicator'] in ['Current reformed smoker for > 15 years',
                                                        'Current reformed smoker for <= 15 years',
                                                        'Current reformed smoker, duration not specified']:
            obs = exposure_observation(obs=copy.deepcopy(smoking_obs), row=row, snomed=None, smoking=True)
        elif "Current smoker" in row['tobacco_smoking_history_indicator']:
            snomed = next((code for code in smoking_snomed_codes if
                           code['note_text'] == "Lifelong non-smoker (<100 cigarettes smoked in lifetime)"), None)
            if snomed:
                obs = exposure_observation(obs=copy.deepcopy(smoking_obs), row=row, snomed=snomed, smoking=True)
        elif "Lifelong non-smoker" in row['tobacco_smoking_history_indicator']:
            snomed = next((code for code in smoking_snomed_codes if
                           code['note_text'] == "Lifelong non-smoker (<100 cigarettes smoked in lifetime)"), None)
            if snomed:
                obs = exposure_observation(obs=copy.deepcopy(smoking_obs), row=row, snomed=snomed, smoking=True)
    if obs:
        return obs


def fhir_alcohol_exposure_observations(row):
    obs = None
    if 'alcohol_history_intensity' in row.keys() and pd.notna(row['alcohol_history_intensity']) and isinstance(
            row['alcohol_history_intensity'], str):
        if 'Daily Drinker' in row['alcohol_history_intensity'] and row['alcohol_history_intensity']:
            snomed = [code for code in alcohol_snomed_codes if code['note_text'] == 'Daily Drinker'][0]
            obs = exposure_observation(obs=copy.deepcopy(alcohol_obs), row=row, snomed=snomed, smoking=False)
        elif 'Social Drinker' in row['alcohol_history_intensity']:
            snomed = [code for code in alcohol_snomed_codes if
                      code['note_text'] == 'Social Drinker (> once a month, < once a week)'][0]
            obs = exposure_observation(obs=copy.deepcopy(alcohol_obs), row=row, snomed=snomed, smoking=False)
        elif 'Weekly Drinker' in row['alcohol_history_intensity']:
            snomed = [code for code in alcohol_snomed_codes if code['note_text'] == 'Weekly Drinker (>=1x a week)'][0]
            obs = exposure_observation(obs=copy.deepcopy(alcohol_obs), row=row, snomed=snomed, smoking=False)
        elif 'Occasional Drinker' in row['alcohol_history_intensity']:
            snomed = \
                [code for code in alcohol_snomed_codes if code['note_text'] == 'Occasional Drinker (< once a month)'][0]
            obs = exposure_observation(obs=copy.deepcopy(alcohol_obs), row=row, snomed=snomed, smoking=False)
    if obs:
        return obs


def fhir_patient(row):
    sex_code = None
    if row['donor_sex'] == "male":
        sex_code = "M"
    elif row['donor_sex'] == "female":
        sex_code = "F"
    patient_gender = None
    if row['donor_sex']:
        patient_gender = row['donor_sex']

    patient = Patient(
        **{"id": str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join([row['icgc_donor_id'], row['project_code']]))),
           "identifier": [Identifier(**{"system": "https://dcc.icgc.org/donor", "value": row['icgc_donor_id']})],
           "gender": patient_gender,
           "extension": [
               {
                   "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex",
                   "valueCode": sex_code
               }]
           })
    return patient


def fhir_research_subject(row):
    patient_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join([row['icgc_donor_id'], row['project_code']])))
    rs_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join([row['icgc_donor_id'], row['project_code']])))
    study_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, row['project_code']))

    return ResearchSubject(
        **{"id": rs_id, "status": "active", "study": Reference(**{"reference": "/".join(["ResearchStudy", study_id])}),
           "subject": Reference(**{"reference": "/".join(["Patient", patient_id])})})


relapse_type = ["distant recurrence/metastasis",
                "local recurrence",
                "local recurrence and distant metastasis",
                "progression (liquid tumours)"]

# for each patient create bodyStructure with either of these general bodySites
body_site_snomed_code = {"Esophagus": "32849002", "Bronchus and lung": "110736001"}
snomed_system = "http://snomed.info/sct"


def fhir_body_structure(row):
    patient_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join([row['icgc_donor_id'], row['project_code']])))

    body_site = None
    if row['project_code'] in ["ESAD-UK", "ESCA-CN"]:
        body_site = {
            "system": "http://snomed.info/sct",
            "code": "32849002",
            "display": "Esophagus"
        }
    elif row['project_code'] in ["LUSC-KR", "LUSC-CN"]:
        body_site = {
            "system": "http://snomed.info/sct",
            "code": "110736001",
            "display": "Bronchus and lung"
        }

    body_structure = BodyStructure(
        **{"id": str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join([row['icgc_donor_id'], row['project_code']]))),
           "includedStructure": [BodyStructureIncludedStructure(**{"structure": {"coding": [body_site]}})],
           "patient": Reference(**{"reference": "/".join(["Patient", patient_id])})
           })
    return body_structure


def get_component(key, value=None, component_type=None):
    if component_type == 'string':
        value = {"valueString": value}
    elif component_type == 'int':
        value = {"valueInteger": value}
    elif component_type == 'float':
        value = {"valueQuantity": {"value": value}}
    elif component_type == 'bool':
        value = {"valueBoolean": value}
    else:
        pass

    component = {
        "code": {
            "coding": [
                {
                    "system": "https://cadsr.cancer.gov/sample_laboratory_observation",
                    "code": key,
                    "display": key
                }
            ],
            "text": key
        }
    }
    if value:
        component.update(value)

    return component


def fhir_condition(row):
    # condition, condition observation, encounter
    icd10 = None
    if row['icgc_donor_id']:
        icd10 = row['donor_diagnosis_icd10'].upper()

    patient_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join([row['icgc_donor_id'], row['project_code']])))
    condition_id = str(uuid.uuid3(uuid.NAMESPACE_DNS,
                                  "".join([row['icgc_donor_id'], row['project_code'], icd10])))

    clinicalStatus = None
    if 'donor_relapse_type' in row.keys() and pd.notna(row['donor_relapse_type']) and row[
        'donor_relapse_type'] in relapse_type:
        clinicalStatus_code = {
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "relapse",
            "display": "Relapse"
        }
        clinicalStatus = CodeableConcept(**{"coding": [clinicalStatus_code], "text": row['donor_relapse_type']})

    elif pd.notna(row['disease_status_last_followup']) and row['disease_status_last_followup'] in [
        'no evidence of disease', 'stable']:
        clinicalStatus_code = {
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "remission",
            "display": "Remission"
        }
        clinicalStatus = CodeableConcept(**{"coding": [clinicalStatus_code], "text": "".join(
            ["Since last follow-up: ", row['disease_status_last_followup']])})

    else:
        clinicalStatus = CodeableConcept(**{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "active",
            "display": "Active"
        }]})

    body_site = None
    if row['project_code'] in ["ESAD-UK", "ESCA-CN"]:
        body_site = CodeableConcept(**{"coding": [{
            "system": "http://snomed.info/sct",
            "code": "32849002",
            "display": "Esophagus"
        }]})
    elif row['project_code'] in ["LUSC-KR", "LUSC-CN"]:
        body_site = CodeableConcept(**{"coding": [{
            "system": "http://snomed.info/sct",
            "code": "110736001",
            "display": "Bronchus and lung"
        }]})

    condition_code = None
    encounter = None
    obs_exam = None
    if 'donor_diagnosis_icd10' in row.keys() and pd.notna(row['donor_diagnosis_icd10']) and re.match(r"^[A-Za-z0-9\-.]+$",
                                                                                       row['donor_diagnosis_icd10']):
        condition_code = CodeableConcept(**{"coding": [{
            "system": "https://terminology.hl7.org/5.1.0/NamingSystem-icd10CM.html",
            "code": str(icd10),
            "display": str(icd10)
        }]})

        encounter = Encounter.construct()
        encounter.status = 'completed'
        encounter.id = str(uuid.uuid3(uuid.NAMESPACE_DNS, "".join(
            [row['icgc_donor_id'], row['project_code'], row['donor_diagnosis_icd10']])))
        encounter.subject = Reference(**{"reference": "/".join(["Patient", patient_id])})

        obs_exam = copy.deepcopy(exam)
        obs_exam["subject"] = {"reference": "/".join(["Patient", patient_id])}
        obs_exam["focus"] = [{"reference": "/".join(["Patient", patient_id])},
                             {"reference": "/".join(["Condition", condition_id])}]

        comp = []
        if row['donor_survival_time'] and isinstance(row['donor_survival_time'], float):
            a_comp = get_component('donor_survival_time', value=row['donor_survival_time'], component_type='float')
            comp.append(a_comp)
        if row['donor_interval_of_last_followup'] and isinstance(row['donor_interval_of_last_followup'], float):
            b_comp = get_component('donor_interval_of_last_followup', value=row['donor_interval_of_last_followup'], component_type='float')
            comp.append(b_comp)
        if comp:
            obs_exam["component"] = comp

        if encounter:
            obs_exam["encounter"] = {"reference": "/".join(["Encounter", encounter.id])}

    age_string = None
    if row['donor_age_at_diagnosis'] and isinstance(row['donor_age_at_diagnosis'], float):
        age_string = str(int(row['donor_age_at_diagnosis']))

    condition = Condition(**{"id": condition_id,
                             "clinicalStatus": clinicalStatus,
                             "subject": Reference(**{"reference": "/".join(["Patient", patient_id])}),
                             "bodySite": [body_site], "code": condition_code, "onsetString": age_string})

    return {"condition": condition, "encounter": encounter, "observation": obs_exam}


def fhir_specimen(row):
    # specimen, specimen Observation
    return


def fhir_medAdmin(row):
    return


patients = [orjson.loads(p.json()) for p in list(df_patient.apply(fhir_patient, axis=1)) if p]
obs_smoking = [os for os in list(df_patient.apply(fhir_smoking_exposure_observations, axis=1)) if os]
obs_alc = [ol for ol in list(df_patient.apply(fhir_alcohol_exposure_observations, axis=1)) if ol]

rsub = [orjson.loads(rs.json()) for rs in list(df_patient.apply(fhir_research_subject, axis=1)) if rs]
rs = [orjson.loads(r.json()) for r in fhir_research_study(df=dat_dict['donor'])]

cond_obs_encont = df_patient.apply(fhir_condition, axis=1)
conditions = [orjson.loads(c['condition'].json()) for c in cond_obs_encont if c['condition']]
encounters = [orjson.loads(c['encounter'].json()) for c in cond_obs_encont if c['encounter']]
obs_exam = [c['observation'] for c in cond_obs_encont if c['observation']]

observations = obs_alc + obs_smoking + obs_exam
observations = list({v['id']: v for v in observations}.values())

body_structures = [orjson.loads(b.json()) for b in list(df_patient.apply(fhir_body_structure, axis=1)) if b]

out_dir = os.path.join(out_path, "META")
if not os.path.exists(out_dir):
    os.makedirs(out_dir)


def fhir_ndjson(entity, out_path):
    if isinstance(entity, list):
        with open(out_path, 'w', encoding='utf8') as file:
            file.write('\n'.join(map(lambda e: json.dumps(e, ensure_ascii=False), entity)))
    else:
        with open(out_path, 'w', encoding='utf8') as file:
            file.write(json.dumps(entity, ensure_ascii=False))


fhir_ndjson(patients, "/".join([out_dir, "Patient.ndjson"]))
print("Successfully converted GDC case info to FHIR's Patient ndjson file!")

fhir_ndjson(rs, "/".join([out_dir, "ResearchStudy.ndjson"]))
print("Successfully converted GDC case info to FHIR's ResearchStudy ndjson file!")

fhir_ndjson(rsub, "/".join([out_dir, "ResearchSubject.ndjson"]))
print("Successfully converted GDC case info to FHIR's ResearchSubject ndjson file!")

fhir_ndjson(observations, "/".join([out_dir, "Observation.ndjson"]))
print("Successfully converted GDC case info to FHIR's Observation ndjson file!")

fhir_ndjson(conditions, "/".join([out_dir, "Condition.ndjson"]))
print("Successfully converted GDC case info to FHIR's Condition ndjson file!")

fhir_ndjson(body_structures, "/".join([out_dir, "BodyStructure.ndjson"]))
print("Successfully converted GDC case info to FHIR's body_structures ndjson file!")

fhir_ndjson(encounters, "/".join([out_dir, "Encounter.ndjson"]))
print("Successfully converted GDC case info to FHIR's Encounter ndjson file!")
