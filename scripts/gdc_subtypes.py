import orjson
import pandas as pd
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