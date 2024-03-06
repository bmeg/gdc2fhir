import re
import json
import orjson
from iteration_utilities import unique_everseen
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
    rs = ResearchStudy.construct()
    if project['ResearchStudyProgressStatus.actual']:
        rs.status = "-".join([project['ResearchStudy.status'], "released"])
    else:
        rs.status = project['ResearchStudy.status']

    if project['ResearchStudy.id'] in ["EXCEPTIONAL_RESPONDERS-ER", "CDDP_EAGLE-1"]:
        rs.id = project['ResearchStudy']['ResearchStudy.id']
    else:
        rs.id = project['ResearchStudy.id']

    rs.name = project['ResearchStudy.name']

    if 'ResearchStudy.identifier' in project.keys() and project['ResearchStudy.identifier']:
        ident = Identifier.construct()
        ident.value = project['ResearchStudy.identifier']
        ident.system = "".join(["https://gdc.cancer.gov/", "project"])
        rs.identifier = [ident]

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

    # assign required fields first
    rs_parent.status = project['ResearchStudy.status']  # child's status?
    rs_parent.id = project['ResearchStudy']['ResearchStudy.id']
    rs_parent.name = project['ResearchStudy']['ResearchStudy.name']

    if 'ResearchStudy.identifier' in project['ResearchStudy'].keys() and project['ResearchStudy']['ResearchStudy.identifier']:
        ident_parent = Identifier.construct()
        ident_parent.value = project['ResearchStudy']['ResearchStudy.identifier']
        ident_parent.system = "".join(["https://gdc.cancer.gov/", "project"])
        rs_parent.identifier = [ident_parent]

    if 'summary' in project.keys():
        rsr = ResearchStudyRecruitment.construct()
        rsr.actualNumber = project['summary']['ResearchStudyRecruitment.actualNumber']
        rs.recruitment = rsr

        e = Extension.construct()
        e.valueUnsignedInt = project['summary'][
            'Extension.valueUnsignedInt']  # total documentReference Count - better association?
        rs.extension = [e]

    ref = Reference(**{"reference": "/".join(["ResearchStudy", project['ResearchStudy']['ResearchStudy.id']])})
    rs.partOf = [ref]
    #  condition -- subject --> patient <--subject-- researchsubject -- study --> researchstudy -- partOf --> researchstudy

    return {'ResearchStudy': rs.json(), "ResearchStudy.partOf": rs_parent.json(), 'ResearchStudy_obj': rs,
            "ResearchStudy.partOf_obj": rs_parent}


# projects_path="./tests/fixtures/project/project_key.ndjson"

def project_gdc_to_fhir_ndjson(out_dir, projects_path):
    projects = utils.load_ndjson(projects_path)
    all_rs = [assign_fhir_for_project(project=p, disease_types=disease_types) for p in projects]
    research_study = [orjson.loads(rs['ResearchStudy_obj'].json()) for rs in all_rs]
    research_study_parent = [orjson.loads(rs['ResearchStudy.partOf_obj'].json()) for rs in all_rs]
    rs_e2f = research_study + list(unique_everseen(research_study_parent)) # ResearchStudy -- *...1  partOf -> ResearchStudy

    with open("".join([out_dir, "/ResearchStudy.ndjson"]), 'w') as file:
        file.write('\n'.join(map(json.dumps, rs_e2f)))


# Case ---------------------------------------------------------------
# load case mapped key values
# cases = utils.load_ndjson("./tests/fixtures/case/case_key.ndjson")
# case = cases[0]

def assign_fhir_for_case(case, disease_types=disease_types, primary_sites=primary_sites, data_dict=data_dict,
                         race=race, ethnicity=ethnicity):
    # create patient **
    patient = Patient.construct()
    patient.id = case['Patient.id']

    if 'Patient.identifier' in case.keys() and case['Patient.identifier'] and re.match(r"^[A-Za-z0-9\-.]+$", case['Patient.identifier']):
        patient_identifier = Identifier.construct()
        patient_identifier.value = case['Patient.identifier']
        patient_identifier.system = "".join(["https://gdc.cancer.gov/", "case"])
        patient.identifier = [patient_identifier]

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
    # project_study_ref_list = []
    # for id in project_relations['ResearchStudy_obj'].id:
    study_ref = Reference(**{"reference": "/".join(["ResearchStudy", project_relations['ResearchStudy_obj'].id])})
    # project_study_ref_list.append(ref)

    subject_ref = Reference(**{"reference": "/".join(["Patient", case['Patient.id']])})

    # create researchSubject to link Patient --> ResearchStudy
    # research_subject_list = []
    # for study_ref in project_study_ref_list:
    research_subject = ResearchSubject.construct()
    research_subject.status = "".join(['unknown-', case['ResearchSubject.status']])
    research_subject.study = study_ref
    research_subject.subject = subject_ref
    # research_subject_list.append(research_subject)

    # create Encounter **
    # TODO: check tissue source site is ok to be encounter
    encounter = None
    encounter_ref = None
    if 'tissue_source_site' in case.keys():
        encounter_tss_id = case['tissue_source_site']['Encounter.id']

        encounter = Encounter.construct()
        # encounter_identifier = Identifier.construct()
        # encounter_identifier.value = encounter_tss_id
        # encounter_identifier.system = "".join(["https://gdc.cancer.gov/", "case"])
        encounter.status = 'completed'
        encounter.id = encounter_tss_id
        encounter.subject = subject_ref

        # encounter_ref = Reference.construct()
        # encounter_ref.type = "Encounter"
        # encounter_ref.identifier = encounter_identifierc

        encounter_ref = Reference(**{"reference": "/".join(["Encounter", encounter_tss_id])})

    observation = None
    observation_ref = None
    if 'diagnoses' in case.keys() and isinstance(case['diagnoses'], list):
         case['diagnoses'] = {k: v for d in case['diagnoses'] for k, v in d.items()}

    if 'diagnoses' in case.keys() and 'Condition.id' in case['diagnoses'].keys():
        obs_identifier = case['diagnoses']['Condition.id']

        # observation_identifier = Identifier.construct()
        # observation_identifier.value = obs_identifier
        # observation_identifier.system = "".join(["https://gdc.cancer.gov/", "case"])

        # create Observation **
        observation = Observation.construct()
        observation.status = 'final'
        observation.subject = subject_ref
        if encounter_ref:
            observation.encounter = encounter_ref
        observation.id = obs_identifier

        observation_code = CodeableConcept.construct()
        observation_code.coding = [{'system': "https://loinc.org/", 'display': "replace-me", 'code': "000000"}]
        observation.code = observation_code

        # observation_ref = Reference.construct()
        # observation_ref.type = "Observation"
        observation_ref = Reference(**{"reference": "/".join(["Observation", observation.id])})

    condition = None # normal tissue don't/shouldn't  have diagnoses or condition
    if 'diagnoses' in case.keys() and 'Condition.id' in case['diagnoses'].keys():

        # create Condition - for each diagnosis_id there is. relation: condition -- assessment --> observation
        condition = Condition.construct()
        condition.id = case['diagnoses']['Condition.id']
        condition_clinicalstatus_code = CodeableConcept.construct()

        if 'display' in case['diagnoses'].keys():
            condition_display = case['diagnoses']['display']
        else:
            condition_display = "replace-me"

        condition_clinicalstatus_code.coding = [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "display": condition_display, "code": "unknown"}]
        condition.clinicalStatus = condition_clinicalstatus_code
        condition.subject = subject_ref
        condition.encounter = encounter_ref

        if 'diagnoses' in case.keys() and 'Condition.onsetAge' in case['diagnoses'].keys():
            condition.onsetString = str(case['diagnoses']['Condition.onsetAge'])

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
                                             'display': case['diagnoses'][key],
                                             'code': data_dict['clinical']['diagnosis']['properties'][staging_name]['termDef'][
                                                 'cde_id']},
                                            {'system': "http://snomed.info/sct",
                                             'display': case['diagnoses'][key],
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
    def add_specimen(dat, name, id_key, has_parent, parent, patient, all_fhir_specimens):
        if name in dat.keys():
            for sample in dat[name]:
                if id_key in sample.keys():
                    fhir_specimen = Specimen.construct()
                    fhir_specimen.id = sample[id_key]
                    fhir_specimen.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})
                    if has_parent:
                        fhir_specimen.parent = [Reference(**{"reference": "/".join(["Specimen", parent.id])})]
                    if fhir_specimen not in all_fhir_specimens:
                        all_fhir_specimens.append(fhir_specimen)

    sample_list = None
    if "samples" in case.keys():
        samples = case["samples"]
        all_samples = []
        all_portions = []
        all_analytes = []
        all_aliquots = []
        for sample in samples:
            if 'Specimen.id.sample' in sample.keys():
                specimen = Specimen.construct()
                specimen.id = sample["Specimen.id.sample"]
                specimen.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})
                if specimen not in all_samples:
                    all_samples.append(specimen)

                add_specimen(dat=sample, name="analytes", id_key="Specimen.id.analyte", has_parent=True,
                             parent=sample, patient=patient, all_fhir_specimens=all_analytes)

                add_specimen(dat=sample, name="aliquots", id_key="Specimen.id.aliquot", has_parent=True,
                             parent=sample, patient=patient, all_fhir_specimens=all_aliquots)

                if "portions" in sample.keys():
                    for portion in sample['portions']:
                        if "Specimen.id.portion" in portion.keys():
                            portion_specimen = Specimen.construct()
                            portion_specimen.id = portion["Specimen.id.portion"]
                            portion_specimen.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})
                            portion_specimen.parent = [Reference(**{"reference": "/".join(["Specimen", specimen.id])})]
                            if portion_specimen not in all_portions:
                                all_portions.append(portion_specimen)

                            if "analytes" in portion.keys():
                                for analyte in portion["analytes"]:
                                    if "Specimen.id.analyte" in analyte.keys():
                                        analyte_specimen = Specimen.construct()
                                        analyte_specimen.id = analyte["Specimen.id.analyte"]
                                        analyte_specimen.subject = Reference(**{"reference": "/".join(["Patient", patient.id])})
                                        analyte_specimen.parent = [Reference(**{"reference": "/".join(["Specimen", portion_specimen.id])})]
                                        if analyte_specimen not in all_analytes:
                                            all_analytes.append(analyte_specimen)

                                        if "aliquots" in analyte.keys():
                                            for aliquot in analyte["aliquots"]:
                                                if "Specimen.id.aliquot" in aliquot.keys():
                                                    aliquot_specimen = Specimen.construct()
                                                    aliquot_specimen.id = aliquot["Specimen.id.aliquot"]
                                                    aliquot_specimen.subject = Reference(
                                                        **{"reference": "/".join(["Patient", patient.id])})
                                                    aliquot_specimen.parent = [Reference(
                                                        **{"reference": "/".join(["Specimen", analyte_specimen.id])})]
                                                    if aliquot_specimen not in all_aliquots:
                                                        all_aliquots.append(aliquot_specimen)

        sample_list = all_samples + all_portions + all_aliquots + all_analytes

    return {'patient': patient, 'encounter': encounter, 'observation': observation, 'condition': condition,
            'project_relations': project_relations, 'research_subject': research_subject, 'specimens': sample_list}


def fhir_ndjson(entity, out_path):
    if isinstance(entity, list):
        with open(out_path, 'w', encoding='utf8') as file:
            file.write('\n'.join(map(lambda e: json.dumps(e, ensure_ascii=False), entity)))
    else:
        with open(out_path, 'w', encoding='utf8') as file:
            file.write(json.dumps(entity, ensure_ascii=False))


def case_gdc_to_fhir_ndjson(out_dir, cases_path):
    cases = utils.load_ndjson(cases_path)
    all_fhir_case_obj = []
    [all_fhir_case_obj.append(assign_fhir_for_case(c)) for c in cases]

    patients = [orjson.loads(fhir_case['patient'].json()) for fhir_case in all_fhir_case_obj]
    encounters = [orjson.loads(fhir_case['encounter'].json()) for fhir_case in all_fhir_case_obj if 'encounter' in fhir_case.keys() and fhir_case['encounter']]
    observations = [orjson.loads(fhir_case['observation'].json()) for fhir_case in all_fhir_case_obj if 'observation' in fhir_case.keys() and fhir_case['observation']]
    conditions = [orjson.loads(fhir_case['condition'].json()) for fhir_case in all_fhir_case_obj if 'condition' in fhir_case.keys() and fhir_case['condition']]
    research_subjects = [orjson.loads(fhir_case['research_subject'].json()) for fhir_case in all_fhir_case_obj]
    projects = [orjson.loads(fhir_case['project_relations']["ResearchStudy_obj"].json()) for fhir_case in all_fhir_case_obj]
    programs = list(unique_everseen([orjson.loads(fhir_case['project_relations']["ResearchStudy.partOf_obj"].json()) for fhir_case in all_fhir_case_obj]))

    specimens = []
    for fhir_case in all_fhir_case_obj:
        if fhir_case["specimens"]:
            for specimen in fhir_case["specimens"]:
                print(specimen.dict())
                specimens.append(orjson.loads(specimen.json()))

    if specimens:
        fhir_ndjson(specimens, "".join([out_dir, "/Specimen.ndjson"]))

    fhir_ndjson(patients, "".join([out_dir, "/Patient.ndjson"]))
    fhir_ndjson(encounters, "".join([out_dir, "/Encounter.ndjson"]))
    fhir_ndjson(observations, "".join([out_dir, "/Observation.ndjson"]))
    fhir_ndjson(conditions, "".join([out_dir, "/Condition.ndjson"]))
    fhir_ndjson(research_subjects, "".join([out_dir, "/ResearchSubject.ndjson"]))
    fhir_ndjson(projects + programs, "".join([out_dir, "/ResearchStudy.ndjson"]))
