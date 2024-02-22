import json
from fhir.resources.identifier import Identifier
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.researchstudy import ResearchStudyRecruitment
from fhir.resources.extension import Extension
from fhir.resources.reference import Reference
from fhir.resources.condition import Condition, ConditionStage
from fhir.resources.observation import Observation
from fhir.resources.encounter import Encounter
from fhir.resources.specimen import Specimen
from fhir.resources.patient import Patient
from fhir.resources.researchsubject import ResearchSubject
from gdc2fhir import utils

disease_types = utils._read_json("./resources/gdc_resources/content_annotations/case/disease_types.json")
primary_sites = utils._read_json("./resources/gdc_resources/content_annotations/case/primary_sites.json")
race = utils._read_json("./resources/gdc_resources/content_annotations/demographic/race.json")
ethnicity = utils._read_json("./resources/gdc_resources/content_annotations/demographic/ethnicity.json")
data_dict = utils.load_data_dictionary("./resources/gdc_resources/data_dictionary/")
cancer_pathological_staging = utils._read_json("./resources/gdc_resources/content_annotations/diagnosis/cancer_pathological_staging.json")


def assign_fhir_for_project(project, disease_types=disease_types):
    # create ResearchStudy
    identifier = Identifier.construct()
    identifier.value = project['ResearchStudy.identifier']

    rs = ResearchStudy.construct()

    # rs.status = "open-released" # assign required fields first
    if project['ResearchStudyProgressStatus.actual']:
        rs.status = "-".join([project['ResearchStudy.status'], "released"])
    else:
        rs.status = project['ResearchStudy.status']

    rs.identifier = [identifier]
    rs.name = project['ResearchStudy.name']

    if 'ResearchStudy.id' in project.keys():
        rs.id = project['ResearchStudy.id']

    l = []
    for c in project['ResearchStudy.condition']:
        for d in disease_types:
            if c in d['value']:
                if d['sctid']:
                    l.append({'system': "http://snomed.info/sct", 'display': d['value'], 'code': d['sctid']})

    cc = CodeableConcept.construct()
    # syntax
    # cc.coding = [{'system': "http://snomed.info/sct", 'code': "115219005", 'display': "Acinar Cell Neoplasms"}]
    cc.coding = l
    rs.condition = [cc]

    # create ResearchStudy -- partOf --> ResearchStudy
    # TODO: check 1..1 relation
    rs_parent = ResearchStudy.construct()
    identifier_parent = Identifier.construct()
    identifier_parent.value = project['ResearchStudy']['ResearchStudy.identifier']

    # assign required fields first
    rs_parent.status = project['ResearchStudy.status']  # child's status?
    rs_parent.name = project['ResearchStudy']['ResearchStudy.name']
    rs_parent.identifier = [identifier_parent]

    if 'summary' in project.keys():
        rsr = ResearchStudyRecruitment.construct()
        rsr.actualNumber = project['summary']['ResearchStudyRecruitment.actualNumber']
        rs.recruitment = rsr

        e = Extension.construct()
        e.valueUnsignedInt = project['summary'][
            'Extension.valueUnsignedInt']  # total documentReference Count - better association?
        rs.extension = [e]

    ref = Reference.construct()
    ref.type = str(ResearchStudy)
    ref.identifier = identifier_parent
    rs.partOf = [ref]
    #  condition -- subject --> patient <--subject-- researchsubject -- study --> researchstudy -- partOf --> researchstudy

    return {'ResearchStudy': rs.json(), "ResearchStudy.partOf": rs_parent.json(), 'ResearchStudy_obj': rs,
            "ResearchStudy.partOf_obj": rs_parent}


# out_path ='./data/ResearchStudy.ndjson'
# projects_path="./tests/fixtures/project_key.ndjson"

def project_gdc_to_fhir_ndjson(out_dir, projects_path):
    projects = utils.load_ndjson(projects_path)
    all_rs = [assign_fhir_for_project(project=p, disease_types=disease_types) for p in projects]
    research_study = [rs['ResearchStudy'] for rs in all_rs]
    research_study_parent = set(
        rs['ResearchStudy.partOf'] for rs in all_rs)  # ResearchStudy -- *...1  partOf -> ResearchStudy
    rs_e2f = research_study + list(research_study_parent)

    with open("".join([out_dir, "/ResearchStudy.ndjson"]), 'w') as file:
        file.write('\n'.join(map(json.dumps, rs_e2f)))


# Case ---------------------------------------------------------------
# load case mapped key values
# cases = utils.load_ndjson("./tests/fixtures/case/case_key.ndjson")
# case = cases[0]

def assign_fhir_for_case(case, disease_types=disease_types, primary_sites=primary_sites, data_dict=data_dict,
                         race=race, ethnicity=ethnicity):
    # create patient **
    patient_identifier = Identifier.construct()
    patient_identifier.value = case['Patient.identifier']

    patient = Patient.construct()
    patient.identifier = [patient_identifier]
    patient.id = case['Patient.id']
    patient.gender = case['demographic']['Patient.gender']
    patient.birthDate = str(case['demographic']['Patient.birthDate'])
    if case['demographic']['Patient.deceasedDateTime']:
        patient.deceasedDateTime = case['demographic']['Patient.deceasedDateTime']

    #  race and ethnicity
    race_ext = Extension.construct()
    race_ext.url = "https://hl7.org/fhir/us/core/STU6/StructureDefinition-us-core-race.json"
    race_ext.valueString = case['demographic']['Extension.extension:USCoreRaceExtension']  # TODO change w FHIR strings

    race_code = ""
    for r in race:
        if r['value'] in case['demographic']['Extension.extension:USCoreRaceExtension']:
            race_code = r['ombCategory-code']

    if race_code:
        race_ext.extension = [{"url": "ombCategory",
                               "valueCoding": {
                                   "system": "urn:oid:2.16.840.1.113883.6.238",
                                   "code": race_code,
                                   "display": case['demographic']['Extension.extension:USCoreRaceExtension']
                               }}]

    ethnicity_ext = Extension.construct()
    ethnicity_ext.url = "http://hl7.org/fhir/us/core/STU6/StructureDefinition-us-core-ethnicity.json"
    ethnicity_ext.valueString = case['demographic']['Extension:extension.USCoreEthnicity']  # TODO change w FHIR strings

    ethnicity_code = ""
    for e in ethnicity:
        if e['value'] in case['demographic']['Extension:extension.USCoreEthnicity']:
            ethnicity_code = e['ombCategory-code']

    if ethnicity_code:
        ethnicity_ext.extension = [{"url": "ombCategory",
                                    "valueCoding": {
                                        "system": "urn:oid:2.16.840.1.113883.6.238",
                                        "code": ethnicity_code,
                                        "display": case['demographic']['Extension:extension.USCoreEthnicity']
                                    }}]
    patient.extension = [ethnicity_ext, race_ext]

    # gdc project for patient
    project_relations = assign_fhir_for_project(project=case['ResearchStudy'], disease_types=disease_types)

    # study Reference link to a ResearchStudy
    project_study_ref_list = []
    for identifier in project_relations['ResearchStudy_obj'].identifier:
        project_study_ref = Reference.construct()
        project_study_ref.type = str(ResearchStudy)
        project_study_ref.identifier = identifier
        project_study_ref_list.append(project_study_ref)

    # subject Reference link to a Patient
    subject_ref = Reference.construct()
    subject_ref.type = str(Patient)
    subject_ref.identifier = patient_identifier

    # create researchSubject to link Patient --> ResearchStudy
    research_subject_list = []
    for study_ref in project_study_ref_list:
        research_subject = ResearchSubject.construct()
        research_subject.status = "".join(['unknown-', case['ResearchSubject.status']])
        research_subject.study = study_ref
        research_subject.subject = subject_ref
        research_subject_list.append(research_subject)

    # create Encounter **
    # TODO: check tissue source site is ok to be encounter
    encounter = Encounter.construct()
    encounter_identifier = Identifier.construct()
    encounter_identifier.value = case['tissue_source_site']['Encounter.identifier']
    encounter.status = 'completed'
    encounter.identifier = [encounter_identifier]
    encounter.subject = subject_ref

    encounter_ref = Reference.construct()
    encounter_ref.type = str(Encounter)
    encounter_ref.identifier = encounter_identifier

    observation_identifier = Identifier.construct()
    observation_identifier.value = case['diagnoses']['Condition.identifier']

    # create Observation **
    observation = Observation.construct()
    observation.status = 'final'
    observation.subject = subject_ref
    observation.encounter = encounter_ref
    observation.identifier = [observation_identifier]

    observation_ref = Reference.construct()
    observation_ref.type = str(Observation)
    # todo explicit observation - or parent observation associated w encounter
    observation_ref.identifier = observation.identifier[0]

    condition_identifier = Identifier.construct()
    condition_identifier.value = case['diagnoses']['Condition.identifier']

    # create Condition - for each diagnosis_id there is. relation: condition -- assessment --> observation
    condition = Condition.construct()
    condition.subject = subject_ref
    condition.encounter = encounter_ref
    # todo: change to fhir type Age - from fhir.resources.age import Age
    # same definition for onsetString: Estimated or actual date,  date-time, or age
    condition.onsetString = str(case['diagnoses']['Condition.onsetAge'])
    # "primary_diagnosis": "Infiltrating duct carcinoma, NOS"
    condition.identifier = [condition_identifier]

    # condition.bodySite <-- primary_site snomed
    l_body_site = []
    for body_site in case['ResearchStudy']['Condition.bodySite']:
        for p in primary_sites:
            if body_site in p['value'] and p['sctid']:
                l_body_site.append({'system': "http://snomed.info/sct", 'display': p['value'], 'code': p['sctid']})

    cc_body_site = CodeableConcept.construct()
    cc_body_site.coding = l_body_site
    condition.bodySite = [cc_body_site]

    # condition staging
    staging_list = []
    for key, value in case['diagnoses'].items():
        if 'Condition.stage_' in key:
            case_stage_display = value
            staging_name = key.replace('Condition.stage_', '')

            sctid_code = None
            stage_type_sctid_code = None
            for dict_item in cancer_pathological_staging:
                if case['diagnoses'][key] == dict_item['value']:
                    sctid_code = dict_item['sctid']
                    stage_type_sctid_code = dict_item['stage_type_sctid']

            cc_stage_type = CodeableConcept.construct()
            cc_stage_type.coding = [{'system': "https://cadsr.cancer.gov/",
                                     'code': data_dict['clinical']['diagnosis']['properties'][staging_name]['termDef'][
                                         'cde_id']},
                                    {'system': "http://snomed.info/sct",
                                     'code': stage_type_sctid_code}
                                    ]

            cc_stage = CodeableConcept.construct()
            cc_stage.coding = [{'system': "https://ncit.nci.nih.gov",
                                'display': case['diagnoses'][key],
                                'code': data_dict['clinical']['diagnosis']['properties'][staging_name]['enumDef'][
                                    case_stage_display]['termDef']['cde_id']
                                }]

            cc_stage_sctid = CodeableConcept.construct()
            cc_stage_sctid.coding = [{'system': "http://snomed.info/sct",
                                      'display': case['diagnoses'][key],
                                      'code': sctid_code}]

            condition_stage = ConditionStage.construct()
            condition_stage.summary = cc_stage
            condition_stage.type = cc_stage_type
            condition_stage.assessment = [observation_ref]
            staging_list.append(condition_stage)

    condition.stage = staging_list

    # relations inside samples list - todo: need to fix traverse_and_map to return ex. [{}, [{[{}, {}]}], {}] cases
    # create specimen
    specimen = Specimen.construct()
    aliquot_specimen = Specimen.construct()
    analyte_specimen = Specimen.construct()
    portion_specimen = Specimen.construct()

    return {'patient': patient, 'encounter': encounter, 'observation': observation, 'condition': condition,
            'project_relations': project_relations, 'research_subject_list': research_subject_list}


def fhir_ndjson(entity, out_path):
    if isinstance(entity, list):
        with open(out_path, 'w') as file:
            file.write('\n'.join(map(json.dumps, entity)))
    else:
        with open(out_path, 'w') as file:
            file.write('\n'.join(map(json.dumps, [entity.json()])))


def case_gdc_to_fhir_ndjson(out_dir, cases_path):
    cases = utils.load_ndjson(cases_path)
    all_fhir_case_obj = []
    [all_fhir_case_obj.append(assign_fhir_for_case(c)) for c in cases]

    patients = [fhir_case['patient'].json() for fhir_case in all_fhir_case_obj]
    encounters = [fhir_case['encounter'].json() for fhir_case in all_fhir_case_obj]
    observations = [fhir_case['observation'].json() for fhir_case in all_fhir_case_obj]
    conditions = [fhir_case['condition'].json() for fhir_case in all_fhir_case_obj]
    research_subjects = [fhir_case['research_subject_list'] for fhir_case in all_fhir_case_obj]
    research_subjects_flatten = [r.json() for rs in research_subjects for r in rs]
    projects = [fhir_case['project_relations']["ResearchStudy_obj"].json() for fhir_case in all_fhir_case_obj]
    programs = list(set([fhir_case['project_relations']["ResearchStudy.partOf_obj"].json() for fhir_case in all_fhir_case_obj]))

    fhir_ndjson(patients, "".join([out_dir, "/Patient.ndjson"]))
    fhir_ndjson(encounters, "".join([out_dir, "/Encounter.ndjson"]))
    fhir_ndjson(observations, "".join([out_dir, "/Observation.ndjson"]))
    fhir_ndjson(conditions, "".join([out_dir, "/Condition.ndjson"]))
    fhir_ndjson(research_subjects_flatten, "".join([out_dir, "/ResearchSubject.ndjson"]))
    fhir_ndjson(projects + programs, "".join([out_dir, "/ResearchStudy.ndjson"]))

