import os.path
import json
from gdc2fhir import utils, gdc_utils
from fhir.resources.researchstudy import ResearchStudyRecruitment

# read in schema and update relations
project_schema_path = "./mapping/project.json"
if os.path.isfile(project_schema_path):
    project_schema = utils.read_json(project_schema_path)

# read in GDC fields and data_dictionaries
fields = gdc_utils.load_fields()
data_dict = gdc_utils.load_data_dictionary()
# ------------------------------
name = project_schema['mappings'][16]['source']['name']
print(name)

# summary.experimental_strategies.case_count -> ResearchStudyRecruitment.actualNumber
project_mapping = project_schema['mappings'][16]

project_mapping["destination"]["name"] = "ResearchStudyRecruitment.actualNumber"
project_mapping["destination"]["title"] = ResearchStudyRecruitment.schema()["properties"]["actualNumber"]["title"]
project_mapping["destination"]["description"] = ResearchStudyRecruitment.schema()["properties"]["actualNumber"]["title"]
project_mapping["destination"]["type"] = ResearchStudyRecruitment.schema()["properties"]["actualNumber"]["type"]
project_mapping["destination"]["module"] = "Administration"

utils.update_values(project_schema, source_name=name, source=True, destination=True, source_values=project_mapping["source"], destination_values=project_mapping["destination"])
# ------------------------------

with open("./mapping/project.json", 'w', encoding='utf-8') as file:
    json.dump(project_schema, file, indent=4)

