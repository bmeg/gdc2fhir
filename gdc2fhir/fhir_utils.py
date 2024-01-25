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


# (load all || point to an existing resource http://hl7.org/fhir/directory.html ) && save in repo for versioning
Coding.schema()['properties']['code']['description']
Patient.schema()['properties']
DocumentReference.schema()['properties']
Observation.schema()['properties']
Extension.schema()['properties']
ResearchStudy.schema()['properties']
GenomicStudyAnalysis.schema()['properties']['changeType']
ResearchSubject.schema()['properties']
Specimen.schema()['properties']['identifier']
# top level description regex
# .replace("Disclaimer: Any field name ends with ``__ext`` doesn't part of\nResource StructureDefinition, instead used to enable Extensibility feature\nfor FHIR Primitive Data Types.\n\n", "")