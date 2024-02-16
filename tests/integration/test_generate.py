import pytest
from gdc2fhir import entity2fhir, utils


@pytest.fixture
def research_study():
    return utils.load_ndjson("./tests/fixtures/ResearchStudy.ndjson")


def test_project_gdc_to_fhir(research_study, out_path='./tests/fixtures/ResearchStudy.ndjson',
                             projects_path="./tests/fixtures/project_key.ndjson"):
    entity2fhir.gdc_to_fhir_ndjson(out_path, projects_path)
    assert research_study == utils.load_ndjson("./tests/fixtures/ResearchStudy.ndjson")

