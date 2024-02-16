import json
from fhir.resources.identifier import Identifier
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.researchstudy import ResearchStudyRecruitment
from fhir.resources.extension import Extension
from fhir.resources.reference import Reference
from fhir.resources.condition import Condition
from gdc2fhir import utils

disease_types = utils._read_json("./resources/gdc_resources/content_annotations/case/disease_types.json")

def assign_fhir(project, disease_types=disease_types):

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

    # TODO: check 1..1 relation
    rs_parent = ResearchStudy.construct()
    identifier_parent = Identifier.construct()
    identifier_parent.value = project['ResearchStudy']['ResearchStudy.identifier']

    # assign required fields first
    rs_parent.status = project['ResearchStudy.status']  # child's status?
    rs_parent.name = project['ResearchStudy']['ResearchStudy.name']
    rs_parent.identifier = [identifier_parent]

    rsr = ResearchStudyRecruitment.construct()
    rsr.actualNumber = project['summary']['ResearchStudyRecruitment.actualNumber']
    rs.recruitment = rsr

    ref = Reference.construct()
    ref.type = str(ResearchStudy)
    ref.identifier = identifier_parent
    rs.partOf = [ref]

    e = Extension.construct()
    e.valueUnsignedInt = project['summary'][
        'Extension.valueUnsignedInt']  # total documetRefence Count - better association?
    rs.extension = [e]

    #  condition -- subject --> patient <--subject-- researchsubject -- study --> researchstudy -- partOf --> researchstudy

    return {'ResearchStudy': rs.json(), "ResearchStudy.partOf": rs_parent.json()}

# out_path ='./data/ResearchStudy.ndjson'
# projects_path="./tests/fixtures/project_key.ndjson"


def gdc_to_fhir_ndjson(out_path, projects_path):
    projects = utils.load_ndjson(projects_path)
    all_rs = [assign_fhir(project=p, disease_types=disease_types) for p in projects]
    research_study = [rs['ResearchStudy'] for rs in all_rs]
    research_study_parent = set(
        rs['ResearchStudy.partOf'] for rs in all_rs)  # ResearchStudy -- *...1  partOf -> ResearchStudy
    rs_e2f = research_study + list(research_study_parent)

    with open(out_path, 'w') as file:
        file.write('\n'.join(map(json.dumps, rs_e2f)))
