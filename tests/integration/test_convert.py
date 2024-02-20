import pytest
import filecmp
from gdc2fhir import mapping, utils


@pytest.fixture
def projects():
    return utils.load_ndjson("./tests/fixtures/projects.ndjson")


def test_project_key_convert(projects):
    mapping.convert_maps(name="project", in_path="./tests/fixtures/projects.ndjson",
                         out_path="./tests/fixtures/project_key_test.ndjson", verbose=True)

    assert filecmp.cmp("./tests/fixtures/project_key_test.ndjson", "./tests/fixtures/project_key.ndjson", shallow=False)
    assert projects == utils.load_ndjson("./tests/fixtures/projects.ndjson")