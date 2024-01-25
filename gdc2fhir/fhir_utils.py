import json
import requests
from bs4 import BeautifulSoup
from fhir.resources.patient import Patient
from fhir.resources.documentreference import DocumentReference
from fhir.resources.coding import Coding
from fhir.resources.observation import Observation
from fhir.resources.observationdefinition import ObservationDefinition
from fhir.resources.extension import Extension
from fhir.resources.researchstudy import ResearchStudy, ResearchStudyRecruitment, ResearchStudyProgressStatus
from fhir.resources.genomicstudy import GenomicStudyAnalysis
from fhir.resources.researchsubject import ResearchSubject
from fhir.resources.specimen import Specimen
from fhir.resources.attachment import Attachment

# https://pypi.org/project/fhir.resources/ version 7.1.0 uses FHIR® (Release R5, version 5.0.0)
version = "5.0.0"

#
Coding.schema()['properties']['code']['description']
Patient.schema()['properties']
DocumentReference.schema()['properties']
Observation.schema()['properties']
Extension.schema()['properties']
ResearchStudy.schema()['properties']
GenomicStudyAnalysis.schema()['properties']['changeType']
ResearchSubject.schema()['properties']
Specimen.schema()['properties']['identifier']


Attachment.schema()['properties']['title']['title']
Attachment.schema()['properties']['size']['title']
Extension.schema()['properties']['valueString']


def clean_description(description):
    """
    top level description regex cleanup

    :param description: fhir class description txt
    :return: cleaned description txt
    """
    return description.replace("Disclaimer: Any field name ends with ``__ext`` doesn't part of\nResource StructureDefinition, instead used to enable Extensibility feature\nfor FHIR Primitive Data Types.\n\n", "")


def get_us_core(path=None, url=None):
    """
    Given a path or url to FHIR Extension.extension:[x] loads in data to map to :[x]

    :param path: Path to json
    :param url: url ex. https://build.fhir.org/ig/HL7/US-Core/StructureDefinition-us-core-ethnicity.json
    :return: TBD
    """

    if path:
        with open(path, 'r') as file:
            for line in file:
                try:
                    json_data = json.loads(line)
                    return json_data
                except json.JSONDecodeError as e:
                    print("Error decoding JSON: {}".format(e))
    elif url:
        response = requests.get(url)

        if response.status_code == 200:
            html_content = response.content.decode("utf-8")
            soup = BeautifulSoup(html_content, 'lxml')
            return soup
    else:
        pass

