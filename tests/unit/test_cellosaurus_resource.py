import os
import pytest
import filecmp
from fhirizer import entity2fhir, utils


@pytest.fixture
def cells_ndjson():
    return "./tests/fixtures/cellosaurus/cellosaurus_cellines.ndjson"


def test_celline_resource(cells_ndjson):
    cells_dir = "./tests/fixtures/cellosaurus/cells/"
    out_dir = "./tests/fixtures/cellosaurus/"

    cls = utils.cellosaurus_cancer_jsons(cells_dir)
    utils.fhir_ndjson(cls, os.path.join(out_dir, "cellosaurus_cellines_test.ndjson"))

    assert filecmp.cmp(cells_ndjson, "./tests/fixtures/cellosaurus/cellosaurus_cellines_test.ndjson", shallow=False)
