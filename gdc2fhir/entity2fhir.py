import re
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
    print("INSIDE assign_fhir_for_project", project)
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

    if l:
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

    if 'Patient.id' in case.keys() and case['Patient.id'] and re.match(r"^[A-Za-z0-9\-.]+$", case['Patient.id']):
        patient.id = case['Patient.id']

    if 'demographic' in case.keys() and 'Patient.birthDate' in case['demographic']:
        patient.birthDate = case['demographic']['Patient.birthDate']

    if 'demographic' in case.keys() and 'Patient.gender' in case['demographic']:
        gender = case['demographic']['Patient.gender']
    else:
        gender = None

    patient.gender = gender
    if 'demographic' in case.keys() and 'Patient.deceasedDateTime' in case['demographic']:
        patient.deceasedDateTime = case['demographic']['Patient.deceasedDateTime']

    race_ethnicity = []
    if 'demographic' in case.keys() and 'Extension.extension:USCoreRaceExtension' in case['demographic'].keys():
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
        race_ethnicity.append(race_ext)

    if 'demographic' in case.keys() and 'Extension:extension.USCoreEthnicity' in case['demographic'].keys():
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

            race_ethnicity.append(ethnicity_ext)

        if race_ethnicity:
            patient.extension = race_ethnicity

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
    encounter = None
    encounter_ref = None
    if 'tissue_source_site' in case.keys():
        encounter_tss_id = case['tissue_source_site']['Encounter.identifier']

        encounter = Encounter.construct()
        encounter_identifier = Identifier.construct()
        encounter_identifier.value = encounter_tss_id
        encounter.status = 'completed'
        encounter.identifier = [encounter_identifier]
        encounter.subject = subject_ref

        encounter_ref = Reference.construct()
        encounter_ref.type = str(Encounter)
        encounter_ref.identifier = encounter_identifier

    observation = None
    observation_ref = None

    # TODO: temporary fix
    if 'diagnoses' in case.keys():
        case['diagnoses'] = {k: v for d in case['diagnoses'] for k, v in d.items()}

    if 'diagnoses' in case.keys() and 'Condition.identifier' in case['diagnoses'].keys():
        obs_identifier = case['diagnoses']['Condition.identifier']

        observation_identifier = Identifier.construct()
        observation_identifier.value = obs_identifier

        # create Observation **
        observation = Observation.construct()
        observation.status = 'final'
        observation.subject = subject_ref
        if encounter_ref:
            observation.encounter = encounter_ref
        observation.identifier = [observation_identifier]

        observation_code = CodeableConcept.construct()
        observation_code.coding = [{'system': "https://loinc.org/", 'display': "replace-me", 'code': "000000"}]
        observation.code = observation_code

        observation_ref = Reference.construct()
        observation_ref.type = str(Observation)
        # todo explicit observation - or parent observation associated w encounter
        observation_ref.identifier = observation.identifier[0]

    condition = None # normal tissue don't/shouldn't  have diagnoses or condition

    if 'diagnoses' in case.keys() and 'Condition.identifier' in case['diagnoses'].keys():
        cond_identifier = case['diagnoses']['Condition.identifier']

        condition_identifier = Identifier.construct()
        condition_identifier.value = cond_identifier

        # create Condition - for each diagnosis_id there is. relation: condition -- assessment --> observation
        condition = Condition.construct()
        condition_clinicalstatus_code = CodeableConcept.construct()
        condition_clinicalstatus_code.coding = [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "unknown" }]
        condition.clinicalStatus = condition_clinicalstatus_code
        condition.subject = subject_ref
        condition.encounter = encounter_ref
        # todo: change to fhir type Age - from fhir.resources.age import Age
        # same definition for onsetString: Estimated or actual date,  date-time, or age

        if 'diagnoses' in case.keys() and 'Condition.onsetAge' in case['diagnoses'].keys():
            condition.onsetString = str(case['diagnoses']['Condition.onsetAge'])
            # "primary_diagnosis": "Infiltrating duct carcinoma, NOS"
            condition.identifier = [condition_identifier]

        # condition.bodySite <-- primary_site snomed
        l_body_site = []
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
                    l_body_site.append({'system': "http://snomed.info/sct", 'display': p['value'], 'code': code})
        # print("l_body_site", l_body_site)

        cc_body_site = CodeableConcept.construct()
        cc_body_site.coding = l_body_site
        condition.bodySite = [cc_body_site]

        if 'diagnoses' in case.keys():
            # condition staging
            staging_list = []
            # print("case['diagnoses']", case['diagnoses'])
            for key, value in case['diagnoses'].items():
                if 'Condition.stage_' in key and value:
                    case_stage_display = value
                    # print("case_stage_display", case_stage_display)
                    staging_name = key.replace('Condition.stage_', '')

                    sctid_code = "0000"
                    stage_type_sctid_code = "0000"
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
                    # print("staging_name:", staging_name, "case_stage_display: ", case_stage_display)
                    if case_stage_display and case_stage_display in data_dict['clinical']['diagnosis']['properties'][staging_name]['enumDef'].keys():
                        code = data_dict['clinical']['diagnosis']['properties'][staging_name]['enumDef'][case_stage_display]['termDef']['cde_id']
                    else:
                        code = "0000"

                    if case['diagnoses'][key]:
                        display = case['diagnoses'][key]
                    else:
                        display = "replace-me"

                    if not re.match("^[^\s]+(\s[^\s]+)*$", sctid_code):
                        sctid_code = "0000"

                    # print("sctid_code", sctid_code)
                    # print("code", code)

                    cc_stage = CodeableConcept.construct()
                    cc_stage.coding = [{'system': "https://ncit.nci.nih.gov",
                                        'display': display,
                                        'code': code
                                        }]

                    cc_stage_sctid = CodeableConcept.construct()
                    cc_stage_sctid.coding = [{'system': "http://snomed.info/sct",
                                              'display': display,
                                              'code': sctid_code}]

                    condition_stage = ConditionStage.construct()
                    condition_stage.summary = cc_stage
                    condition_stage.type = cc_stage_type
                    if observation_ref:
                        condition_stage.assessment = [observation_ref]
                    staging_list.append(condition_stage)

            condition.stage = staging_list

    # create specimen
    specimen = Specimen.construct()
    aliquot_specimen = Specimen.construct()
    analyte_specimen = Specimen.construct()
    portion_specimen = Specimen.construct()

    return {'patient': patient, 'encounter': encounter, 'observation': observation, 'condition': condition,
            'project_relations': project_relations, 'research_subject_list': research_subject_list}


def fhir_ndjson(entity, out_path):
    if isinstance(entity, list):
        with open(out_path, 'w', encoding='utf8') as file:
            file.write('\n'.join(map(lambda e: json.dumps(e, ensure_ascii=False), entity)))
    else:
        with open(out_path, 'w', encoding='utf8') as file:
            file.write(json.dumps(entity.json(), ensure_ascii=False))


def case_gdc_to_fhir_ndjson(out_dir, cases_path):
    cases = utils.load_ndjson(cases_path)
    all_fhir_case_obj = []
    [all_fhir_case_obj.append(assign_fhir_for_case(c)) for c in cases]

    patients = [json.loads(fhir_case['patient'].json()) for fhir_case in all_fhir_case_obj]
    encounters = [json.loads(fhir_case['encounter'].json()) for fhir_case in all_fhir_case_obj if 'encounter' in fhir_case.keys() and fhir_case['encounter']]
    observations = [json.loads(fhir_case['observation'].json()) for fhir_case in all_fhir_case_obj if 'observation' in fhir_case.keys() and fhir_case['observation']]
    conditions = [json.loads(fhir_case['condition'].json()) for fhir_case in all_fhir_case_obj if 'condition' in fhir_case.keys() and fhir_case['condition']]
    research_subjects = [fhir_case['research_subject_list'] for fhir_case in all_fhir_case_obj]
    research_subjects_flatten = [json.loads(r.json()) for rs in research_subjects for r in rs]
    projects = [json.loads(fhir_case['project_relations']["ResearchStudy_obj"].json()) for fhir_case in all_fhir_case_obj]
    programs = list(set([fhir_case['project_relations']["ResearchStudy.partOf_obj"].json() for fhir_case in all_fhir_case_obj]))

    fhir_ndjson(patients, "".join([out_dir, "/Patient.ndjson"]))
    fhir_ndjson(encounters, "".join([out_dir, "/Encounter.ndjson"]))
    fhir_ndjson(observations, "".join([out_dir, "/Observation.ndjson"]))
    fhir_ndjson(conditions, "".join([out_dir, "/Condition.ndjson"]))
    fhir_ndjson(research_subjects_flatten, "".join([out_dir, "/ResearchSubject.ndjson"]))
    fhir_ndjson(projects + programs, "".join([out_dir, "/ResearchStudy.ndjson"]))
