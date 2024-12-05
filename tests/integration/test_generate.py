import pytest
from fhirizer import entity2fhir, utils


@pytest.fixture
def research_study():
    return utils.load_ndjson("./tests/fixtures/project/META/ResearchStudy.ndjson")


@pytest.fixture
def patient():
    return utils.load_ndjson("./tests/fixtures/case/META/Patient.ndjson")


@pytest.fixture
def condition():
    return utils.load_ndjson("./tests/fixtures/case/META/Condition.ndjson")


def test_project_gdc_to_fhir(research_study, name='project', out_dir='./tests/fixtures/project/META',
                             projects_path="./tests/fixtures/project/projects.ndjson"):
    entity2fhir.project_gdc_to_fhir_ndjson(out_dir=out_dir, name=name, projects_path=projects_path, convert=False, verbose=False)
    assert research_study == utils.load_ndjson("./tests/fixtures/project/META/ResearchStudy.ndjson")


def test_case_gdc_to_fhir(patient, condition, name='case', out_dir='./tests/fixtures/case/META',
                          cases_path="./tests/fixtures/case/cases.ndjson"):
    entity2fhir.case_gdc_to_fhir_ndjson(out_dir=out_dir, name=name, cases_path=cases_path, convert=False, verbose=False)
    assert patient == utils.load_ndjson("./tests/fixtures/case/META/Patient.ndjson")
    assert condition == utils.load_ndjson("./tests/fixtures/case/META/Condition.ndjson")


