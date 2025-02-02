import orjson
import pandas as pd
import numpy as np
import importlib.resources
from pathlib import Path
from fhirizer import utils
from fhir.resources.observation import Observation
from fhir.resources.identifier import Identifier
from uuid import uuid3, NAMESPACE_DNS

project_id = "GDC"
NAMESPACE_GDC = uuid3(NAMESPACE_DNS, 'gdc.cancer.gov')

out_dir = "projects/GDC/TCGA-BRCA/META"
cancer_cohort = 'BRCA'

path = str(Path(importlib.resources.files('fhirizer').parent / 'data' / 'TMP_20230209' / 'BRCA_v12_20210228.tsv'))
cases_path = str(Path(importlib.resources.files('fhirizer').parent / 'data' / 'brca_cases.ndjson'))

cancer2subtype = utils._read_json(str(Path(importlib.resources.files('fhirizer').parent / 'data' / 'cancer2name.json')))
_this_cancer_subtypes = cancer2subtype[cancer_cohort]

# GDC molecular subtypes
# https://gdc.cancer.gov/about-data/publications/CCG-TMP-2022
df = pd.read_csv(path, sep="\t")
df['Labels'].replace(_this_cancer_subtypes, inplace=True)

cases = utils.load_ndjson(cases_path)

_id_maps = {}
[_id_maps.update({case['submitter_id']: case['id']}) for case in cases]


def create_observation(id_maps, submitter_id, id, subtype, case_identifier) -> Observation:
    """ Creates Cancer Subtype Observations via Cancer Cell TMP paper metadata:

    _submitter_id = 'TCGA-AO-A0JC'
    _case_identifier = Identifier(**{"value": _id_maps[_submitter_id], "system": "".join(["https://gdc.cancer.gov/", "case_id"]), "use": "official"})
    _id = utils.mint_id(identifier=_case_identifier, resource_type="Patient", project_id=project_id, namespace=NAMESPACE_GDC)
    _subtype = str(df['Labels'][df[cancer_cohort].isin([_submitter_id])].values[0])

    """
    _observation_dict = {
      "id": "1234",
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
            "system": "http://purl.obolibrary.org/obo",
            "code": "NCIT_C185941",
            "display": "Disease Molecular Subtype Qualifier"
          }
        ]
      },
      "subject": {
        "reference": f"Patient/{id}"
      },
      "focus": [{
        "reference": f"Patient/{id}"
      }],
      "valueString": subtype
    }

    _obs_identifier = Identifier(
        **{
            "system": "".join(["https://gdc.cancer.gov/", "subtype"]),
            "value": "/".join([id_maps[submitter_id], subtype]),
            "use": "official"
        }
    )
    _obs_id = utils.mint_id(
        identifier=[_obs_identifier, case_identifier], resource_type="Observation",
        project_id=project_id,
        namespace=NAMESPACE_GDC)

    _obs = Observation(**_observation_dict)
    _obs.id = _obs_id
    _obs.identifier = [_obs_identifier]

    return _obs


subtype_observations = []
for index, row in df.iterrows():
    _submitter_id = row[cancer_cohort]
    _case_identifier = Identifier(
        **{"value": _id_maps[_submitter_id], "system": "".join(["https://gdc.cancer.gov/", "case_id"]),
           "use": "official"})
    _id = utils.mint_id(identifier=_case_identifier, resource_type="Patient", project_id=project_id,
                        namespace=NAMESPACE_GDC)
    _subtype = str(df['Labels'][df[cancer_cohort].isin([_submitter_id])].values[0])
    observation = create_observation(id_maps=_id_maps, submitter_id=_submitter_id, id=_id, subtype=_subtype, case_identifier=_case_identifier)
    if observation:
        subtype_observations.append(observation)


if subtype_observations:
    observations_list = [orjson.loads(o.model_dump_json()) for o in subtype_observations]
    observations_list = list({v['id']: v for v in observations_list}.values())
    if observations_list:
        utils.create_or_extend(new_items=observations_list, folder_path=out_dir, resource_type='Observation', update_existing=False)

"""
# subtypes - query FHIRized data via grip and build a df for downstream analysis 

import pandas as pd
import sys
import gripql

conn = gripql.Connection("http://localhost:8201")
G = conn.graph("gdc_brca")

subtypes = G.query().V().hasLabel("Observation").as_("observation").unwind("$.code").unwind("$.code.coding").has(gripql.eq("$.code.coding.code", "NCIT_C185941")).execute()
subtypes_patients = G.query().V().hasLabel("Observation").as_("observation").unwind("$.code").unwind("$.code.coding").has(gripql.eq("$.code.coding.code", "NCIT_C185941")).out("focus_Patient").execute()
patient_data = subtypes_patients[0]['data']


def expand_metadata(patient_data) -> dict:
    if 'extension' in patient_data.keys():
        race = next((ext['valueString'] for ext in patient_data['extension'] if 'us-core-race' in ext['url']), None)
        ethnicity = next((ext['valueString'] for ext in patient_data['extension'] if 'us-core-ethnicity' in ext['url']), None)
        age = next((ext['valueQuantity']['value'] for ext in patient_data['extension'] if 'Patient-age' in ext['url']), None)
    else:
        race = None
        ethnicity = None
        age = None

    if "identifier" in patient_data:
        secondary_identifier = next((iden['value'] for iden in patient_data['identifier'] if iden['use'] == 'secondary'), None)
        official_identifier = next((iden['value'] for iden in patient_data['identifier'] if iden['use'] == 'official'), None)
    else:
        secondary_identifier = None
        official_identifier = None

    if "gender" in patient_data.keys():
        gender = patient_data['gender']
    else:
        gender = None

    if 'deceasedBoolean' in patient_data.keys():
        deseased = patient_data['deceasedBoolean']
    else:
        deseased = None

    expanded_info = {
        'id': patient_data['id'],
        'gender': gender,
        'race': race,
        'ethnicity': ethnicity,
        'age': age,
        'secondary_identifier': secondary_identifier,
        'official_identifier': official_identifier,
        'deceased': deseased
    }
    return expanded_info

df = pd.DataFrame([expand_metadata(dat['data']) for dat in subtypes_patients])
df['age']= df['age'].fillna(0).astype(np.int64)

l = []
for item in subtypes:
    if 'valueString' in item['data'].keys():
        l.append(item['data']['valueString'])

df['subtype'] = l
df.to_csv("subtypes_df.csv", index=False)
"""
