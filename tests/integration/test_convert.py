import pytest
import filecmp
from gdc2fhir import mapping, utils


@pytest.fixture
def projects():
    return utils.load_gdc_scripts_ndjson("./tests/fixtures/projects.ndjson")


def test_project_key_convert(projects):
    mapping.convert_maps(name="project", in_path="./tests/fixtures/projects.ndjson",
                         out_path="./tests/fixtures/project_key_test.json")

    assert filecmp.cmp("./tests/fixtures/project_key_test.json", "./tests/fixtures/project_key.json", shallow=False)
    assert projects == utils.load_gdc_scripts_ndjson("./tests/fixtures/projects.ndjson")