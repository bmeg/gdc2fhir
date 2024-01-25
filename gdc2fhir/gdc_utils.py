import json
import requests
from bs4 import BeautifulSoup


def get_field_text(table):
    """
    Gets text of td tags of an xml table

    :param table: xml data in an html table
    :return: list of GDC fields
    """
    fields = []
    rows = table.find_all("td", recursive=True)
    for td in rows:
        fields.append(td.get_text())
    return fields


def gdc_available_fields(save=True):
    """
    Fetch available fields via GDC site

    :return: Dictionary of project, case, and file fields
    """
    response = requests.get("https://docs.gdc.cancer.gov/API/Users_Guide/Appendix_A_Available_Fields/")

    if response.status_code == 200:
        html_content = response.content.decode("utf-8")

        soup = BeautifulSoup(html_content, 'lxml')
        field_tables = soup.find_all("table", recursive=True)
        project_fields = get_field_text(field_tables[0])
        case_fields = get_field_text(field_tables[1])
        file_fields = get_field_text(field_tables[2])
        annotation_fields = get_field_text(field_tables[3])
        convention_supplement = get_field_text(field_tables[8])  # make dict
        fields = {"project_fields": project_fields, "case_fields": case_fields, "file_fields": file_fields,
                  "annotation_fields": annotation_fields, "convention_supplement": convention_supplement}
        if save:
            for k, v in fields.items():
                jr = json.dumps(v, indent=4)
                out_path = "".join(["./resources/gdc_resources/fields/", k, ".json"])
                with open(out_path, "w") as output_file:
                    output_file.write(jr)
        return fields
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


# TODO: other methods vs API get call data fetch
def gdc_data_dict(entity_name):
    """
    Fetches data dictionary for a specified entity from GDC API.
    TODO: pass version - or get data dict from python client

    :param entity_name: Name of GDC entity ex. project, case, file, annotation
    :return: Json schema data dictionary for the entity - none if error occurs
    """
    api_url = f"https://api.gdc.cancer.gov/v0/submission/_dictionary/{entity_name}"
    response = requests.get(api_url)

    if response.status_code == 200:
        entity_data = response.json()
        return entity_data
    else:
        print(f"Error: Unable to fetch data for entity {entity_name}. Status code: {response.status_code}")
        return None


def gdc_api_version_data_info(api_version="v0"):
    api_url = f"https://api.gdc.cancer.gov/{api_version}/status"
    response = requests.get(api_url)

    if response.status_code == 200:
        version_dict = response.json()
        version_dict['source_version'] = version_dict.pop('version')
        return version_dict


# (load all || point to an existing resource ? if there are any ) && save in repo for versioning
demographic_dict = gdc_data_dict("demographic")
project_dict = gdc_data_dict("project")
case_dict = gdc_data_dict("case")
file_dict = gdc_data_dict("file")
annotations_dict = gdc_data_dict("annotations")


# primary_sites = case_dict['properties']['primary_site']['enum']
# disease_types = case_dict['properties']['disease_type']['enum']




