import os
from typing import List, LiteralString
from gdc2fhir import utils
from gdc2fhir.schema import Map, Source, Destination, Reference
from fhir.resources.patient import Patient
from fhir.resources.identifier import Identifier
from fhir.resources.coding import Coding
from fhir.resources.observation import Observation
from fhir.resources.observationdefinition import ObservationDefinition
from fhir.resources.extension import Extension
from fhir.resources.researchstudy import ResearchStudy, ResearchStudyRecruitment, ResearchStudyProgressStatus
from fhir.resources.researchsubject import ResearchSubject
from fhir.resources.specimen import Specimen
from fhir.resources.imagingstudy import ImagingStudy
from fhir.resources.annotation import Annotation
from fhir.resources.condition import Condition
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.range import Range
from fhir.resources.documentreference import DocumentReference
from fhir.resources.attachment import Attachment

two_level_up = os.path.abspath(os.path.join(os.path.dirname('__file__'), '../..'))
case_schema = utils.load_schema_from_json(path="".join([two_level_up, "/mapping/case.json"]))
keys_to_label_fields = [key for key in case_schema.obj_keys if
                        key not in [x.source.name for x in case_schema.mappings]]
data_dict = utils.load_data_dictionary("".join([two_level_up, "/resources/gdc_resources/data_dictionary/"]))

"""
Field labels mapped semi-computationally 

Map(
    source=Source(
        name='',
        description='',
        description_url='',
        category='',
        type='',
        enums=[],
        content_annotation=[],
        reference=[]

    ),
    destination=Destination(
        name='',
        description='',
        description_url='',
        module='',
        title='',
        type='',
        format='',
        reference=''
    )
)

# days_to_index -> ?
# annotations -> Extension or Annotation in FHIR - skipping to focus on current script
# demographic -> Patient
# case -> Patient
# demographic.gender needs Coding.code for gender 
"""

case_maps = []

Map(
    source=Source(
        name='aliquot_ids',
        description=data_dict["biospecimen"]["aliquot"]["properties"]["id"]["common"]["description"],
        category=data_dict["biospecimen"]["aliquot"]["category"],
        type=data_dict["biospecimen"]["aliquot"]["properties"]["id"]["type"],
        reference=[
            Reference(reference_type=data_dict["biospecimen"]["aliquot"]["links"][0]["subgroup"][0]["target_type"]),
            Reference(reference_type=data_dict["biospecimen"]["aliquot"]["links"][0]["subgroup"][1]["target_type"])]
    ),
    destination=Destination(
        name='Specimen.identifier',
        description=Specimen.schema()["properties"]["identifier"]["description"],
        module='Diagnostics',
        title=Specimen.schema()["properties"]["identifier"]["title"],
        type=Specimen.schema()["properties"]["identifier"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='analyte_ids',
        description=data_dict["biospecimen"]["analyte"]["properties"]["id"]["common"]["description"],
        category=data_dict["biospecimen"]["analyte"]["category"],
        type=data_dict["biospecimen"]["analyte"]["properties"]["id"]["type"],
        reference=[
            Reference(reference_type=data_dict["biospecimen"]["analyte"]["links"][0]["subgroup"][0]["target_type"]),
            Reference(reference_type=data_dict["biospecimen"]["analyte"]["links"][0]["subgroup"][1]["target_type"])]
    ),
    destination=Destination(
        name='Specimen.identifier',
        description=Specimen.schema()["properties"]["identifier"]["description"],
        module='Diagnostics',
        title=Specimen.schema()["properties"]["identifier"]["title"],
        type=Specimen.schema()["properties"]["identifier"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='case_id',
        description=data_dict["case"]["case"]["properties"]["id"]["common"]["description"],
        category=data_dict["case"]["case"]["category"],
        type=data_dict["case"]["case"]["properties"]["id"]["common"]["termDef"]["term"],
        reference=[Reference(reference_type=data_dict["case"]["case"]["links"][0]["target_type"]),
                   Reference(reference_type=data_dict["case"]["case"]["links"][1]["target_type"])]
    ),
    destination=Destination(
        name='Patient.identifier',
        description=Patient.schema()["properties"]['identifier']["title"],
        module='Administration',
        title=Patient.schema()["properties"]['identifier']["title"],
        type=Patient.schema()["properties"]['identifier']["type"]
    )
)

Map(
    source=Source(
        name='created_datetime',
        description=data_dict["clinical"]["diagnosis"]["properties"]["created_datetime"]["common"]["description"],
        category=data_dict["clinical"]["diagnosis"]["category"],
        format=data_dict["clinical"]["diagnosis"]["properties"]["created_datetime"]["oneOf"][0]["format"],
        type=data_dict["clinical"]["diagnosis"]["properties"]["created_datetime"]["oneOf"][0]["type"]
    ),
    destination=Destination(
        name='DiagnosticReport.issued',
        description=DiagnosticReport.schema()["properties"]["issued"]["description"],
        module='Diagnostics',
        title=DiagnosticReport.schema()["properties"]["issued"]["title"],
        type=DiagnosticReport.schema()["properties"]["issued"]["type"]
    )
)

Map(
    source=Source(
        name='portion_ids',
        description=data_dict["biospecimen"]["portion"]["properties"]["id"]["common"]["description"],
        category=data_dict["biospecimen"]["portion"]["category"],
        type=data_dict["biospecimen"]["portion"]["properties"]["id"]["type"]
    ),
    destination=Destination(
        name='Specimen.identifier',
        description=Specimen.schema()["properties"]["identifier"]["description"],
        module='Diagnostics',
        title=Specimen.schema()["properties"]["identifier"]["title"],
        type=Specimen.schema()["properties"]["identifier"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='sample_ids',
        description=data_dict["biospecimen"]["sample"]["properties"]["id"]["common"]["description"],
        category=data_dict["biospecimen"]["sample"]["category"],
        type=data_dict["biospecimen"]["sample"]["properties"]["id"]["common"]["termDef"]["term"],
        reference=[Reference(reference_type=data_dict["biospecimen"]["sample"]["links"][0]["target_type"]),
                   Reference(reference_type=data_dict["biospecimen"]["sample"]["links"][1]["target_type"]),
                   Reference(reference_type=data_dict["biospecimen"]["sample"]["links"][2]["target_type"]),
                   Reference(reference_type=data_dict["biospecimen"]["sample"]["links"][3]["target_type"])]
    ),
    destination=Destination(
        name='Specimen.identifier',
        description=Specimen.schema()["properties"]["identifier"]["description"],
        module='Diagnostics',
        title=Specimen.schema()["properties"]["identifier"]["title"],
        type=Specimen.schema()["properties"]["identifier"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='slide_ids',
        description=data_dict["biospecimen"]["slide"]["properties"]["id"]["common"]["description"],
        category=data_dict["biospecimen"]["slide"]["category"],
        type=data_dict["biospecimen"]["slide"]["properties"]["id"]["type"]
    ),
    destination=Destination(
        name='ImagingStudy.identifier',
        description=ImagingStudy.schema()["properties"]["identifier"]["description"],
        module='',
        title=ImagingStudy.schema()["properties"]["identifier"]["title"],
        type=ImagingStudy.schema()["properties"]["identifier"]["items"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='state',
        description=data_dict["case"]["case"]["properties"]["state"]["common"]["description"],
        category=data_dict["case"]["case"]["category"],
        type='string'
    ),
    destination=Destination(
        name='ResearchSubject.status',
        description=ResearchSubject.schema()["properties"]["status"]["description"],
        module='',
        title=ResearchSubject.schema()["properties"]["status"]["title"],
        type=ResearchSubject.schema()["properties"]["status"]["type"]
    )
)

Map(
    source=Source(
        name='submitter_aliquot_ids',
        description=data_dict["biospecimen"]["aliquot"]["properties"]["submitter_id"]["description"],
        category=data_dict["biospecimen"]["aliquot"]["category"],
        type=data_dict["biospecimen"]["aliquot"]["properties"]["submitter_id"]["type"]
    ),
    destination=Destination(
        name='Specimen.id',
        description=Specimen.schema()["properties"]["id"]["description"],
        module='Diagnostics',
        title=Specimen.schema()["properties"]["id"]["title"],
        type=Specimen.schema()["properties"]["id"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='submitter_aliquot_ids',
        description=data_dict["biospecimen"]["analyte"]["properties"]["submitter_id"]["description"],
        category=data_dict["biospecimen"]["analyte"]["category"],
        type=data_dict["biospecimen"]["analyte"]["properties"]["submitter_id"]["type"]
    ),
    destination=Destination(
        name='Specimen.id',
        description=Specimen.schema()["properties"]["id"]["description"],
        module='Diagnostics',
        title=Specimen.schema()["properties"]["id"]["title"],
        type=Specimen.schema()["properties"]["id"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='submitter_id',
        description=data_dict["case"]["case"]["properties"]["submitter_id"]["description"],
        category=data_dict["case"]["case"]["category"],
        type=data_dict["case"]["case"]["properties"]["submitter_id"]["type"]

    ),
    destination=Destination(
        name='Patient.id',
        description=Patient.schema()["properties"]['id']["description"],
        module='Administration',
        title=Patient.schema()["properties"]['id']["title"],
        type=Patient.schema()["properties"]['id']["type"]
    )
)

Map(
    source=Source(
        name='submitter_portion_ids',
        description=data_dict["biospecimen"]["portion"]["properties"]["submitter_id"]["description"],
        category=data_dict["biospecimen"]["portion"]["category"],
        type=data_dict["biospecimen"]["portion"]["properties"]["submitter_id"]["type"]
    ),
    destination=Destination(
        name='Specimen.id',
        description=Specimen.schema()["properties"]["id"]["description"],
        module='Diagnostics',
        title=Specimen.schema()["properties"]["id"]["title"],
        type=Specimen.schema()["properties"]["id"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='submitter_sample_ids',
        description=data_dict["biospecimen"]["sample"]["properties"]["submitter_id"]["description"],
        category=data_dict["biospecimen"]["sample"]["category"],
        type=data_dict["biospecimen"]["sample"]["properties"]["submitter_id"]["type"]
    ),
    destination=Destination(
        name='Specimen.id',
        description=Specimen.schema()["properties"]["id"]["description"],
        module='Diagnostics',
        title=Specimen.schema()["properties"]["id"]["title"],
        type=Specimen.schema()["properties"]["id"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='submitter_slide_ids',
        description=data_dict["biospecimen"]["slide"]["properties"]["submitter_id"]["description"],
        category=data_dict["biospecimen"]["slide"]["category"],
        type=data_dict["biospecimen"]["slide"]["properties"]["submitter_id"]["type"]
    ),
    destination=Destination(
        name='ImagingStudy.id',
        description=ImagingStudy.schema()["properties"]["id"]["description"],
        module='Diagnostics',
        title=ImagingStudy.schema()["properties"]["id"]["title"],
        type=ImagingStudy.schema()["properties"]["id"]["type"],
        format=str(List[Identifier])
    )
)

Map(
    source=Source(
        name='updated_datetime',
        description=data_dict["case"]["case"]["properties"]["updated_datetime"]["common"]["description"],
        category=data_dict["case"]["case"]["category"],
        type=data_dict["case"]["case"]["properties"]["updated_datetime"]["oneOf"][0]["type"],
        format=data_dict["case"]["case"]["properties"]["updated_datetime"]["oneOf"][0]["format"]

    ),
    destination=Destination(
        name='Extension.valueDateTime',
        description=Extension.schema()["properties"]["valueDateTime"]["description"],
        description_url='https://build.fhir.org/datatypes.html#dateTime',
        module='Extensibility',
        title=Extension.schema()["properties"]["valueDateTime"]["title"],
        type=Extension.schema()["properties"]["valueDateTime"]["type"]
    )
)

Map(
    source=Source(
        name='demographic.created_datetime',
        description=data_dict["clinical"]["demographic"]["properties"]["created_datetime"]["common"]["description"],
        description_url='https://docs.gdc.cancer.gov/Data_Dictionary/viewer/#?view=table-definition-view&id=demographic',
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["created_datetime"]["oneOf"][0]["type"],
        format=data_dict["clinical"]["demographic"]["properties"]["created_datetime"]["oneOf"][0]["format"]
    ),
    destination=Destination(
        name='Extension.valueDateTime',
        description=Extension.schema()["properties"]["valueDateTime"]["description"],
        description_url='https://build.fhir.org/datatypes.html#dateTime',
        module='Foundation',
        title=Extension.schema()["properties"]["valueDateTime"]["title"],
        type=Extension.schema()["properties"]["valueDateTime"]["type"],
        format=Extension.schema()["properties"]["valueDateTime"]["format"]
    )
)

Map(
    source=Source(
        name='demographic.demographic_id',
        description=data_dict["clinical"]["demographic"]["properties"]["id"]["common"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["id"]["common"]["termDef"]["term"]
    ),
    destination=Destination(
        name='Patient.identifier',
        description=Patient.schema()["properties"]['identifier']["title"],
        module='Administration',
        title=Patient.schema()["properties"]['identifier']["title"],
        type=Patient.schema()["properties"]['identifier']["type"]
    )
)

Map(
    source=Source(
        name='demographic.ethnicity',
        description=data_dict["clinical"]["demographic"]["properties"]["ethnicity"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["ethnicity"]["termDef"]["term"],
        enums=[{'enum': ['hispanic or latino',
                         'not hispanic or latino',
                         'Unknown',
                         'unknown',
                         'not reported',
                         'not allowed to collect']}],
        content_annotation="@gdc2fhir/resources/gdc_resources/content_annotations/demographic/ethnicity.json"
    ),
    destination=Destination(
        name='Extension:extension.USCoreEthnicity',
        description='Concepts classifying the person into a named category of humans sharing common history, traits, '
                    'geographical origin or nationality. The race codes used to represent these concepts are based '
                    'upon the CDC Race and Ethnicity Code Set Version 1.0 which includes over 900 concepts for '
                    'representing race and ethnicity of which 921 reference race. The race concepts are grouped by '
                    'and pre-mapped to the 5 OMB race categories.',
        description_url='https://build.fhir.org/ig/HL7/US-Core/StructureDefinition-us-core-ethnicity.profile.json.html',
        module='Foundation',
        title=Extension.schema()["properties"]["extension"]["title"],
        type=Extension.schema()["properties"]["extension"]["type"]
    )
)

Map(
    source=Source(
        name='demographic.gender',
        description=data_dict["clinical"]["demographic"]["properties"]["gender"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["gender"]["termDef"]["term"],
        enums=[{'enum': ['female', 'male', 'unspecified', 'unknown', 'not reported']}],
        content_annotation="@gdc2fhir/resources/gdc_resources/content_annotations/demographic/gender.json"
    ),
    destination=Destination(
        name='Patient.gender',
        description=Patient.schema()["properties"]['gender']["description"],
        module='Administration',
        title=Patient.schema()["properties"]['gender']["title"],
        type=Patient.schema()["properties"]['gender']["type"]
    )
)

Map(
    source=Source(
        name='demographic.race',
        description=data_dict["clinical"]["demographic"]["properties"]["race"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["race"]["termDef"]["term"],
        enums=[{'enum': ['american indian or alaska native',
                         'asian',
                         'black or african american',
                         'native hawaiian or other pacific islander',
                         'white',
                         'other',
                         'Unknown',
                         'unknown',
                         'not reported',
                         'not allowed to collect']}],
        content_annotation="@gdc2fhir/resources/gdc_resources/content_annotations/demographic/race.json"
    ),
    destination=Destination(
        name='Extension.extension:USCoreRaceExtension',
        description='Concepts classifying the person into a named category of humans sharing common history, traits, '
                    'geographical origin or nationality. The race codes used to represent these concepts are based '
                    'upon the CDC Race and Ethnicity Code Set Version 1.0 which includes over 900 concepts for '
                    'representing race and ethnicity of which 921 reference race. The race concepts are grouped by '
                    'and pre-mapped to the 5 OMB race categories.',
        description_url='http://hl7.org/fhir/us/core/STU6.1/StructureDefinition-us-core-race.profile.json.html',
        module='Foundation',
        title=Extension.schema()["properties"]["extension"]["title"],
        type=Extension.schema()["properties"]["extension"]["type"]
    )
)

Map(
    source=Source(
        name='demographic.state',
        description=data_dict["clinical"]["demographic"]["properties"]["state"]["common"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type='string',
        enums=[{'enum': ['uploading',
                         'uploaded',
                         'md5summing',
                         'md5summed',
                         'validating',
                         'error',
                         'invalid',
                         'suppressed',
                         'redacted',
                         'live']},
               {'enum': ['validated', 'submitted', 'released']}]

    ),
    destination=Destination(
        name='Extension.valueString',
        description=Extension.schema()["properties"]["valueString"]["description"],
        description_url='',
        module='Foundation',
        title=Extension.schema()["properties"]["extension"]["title"],
        type=Extension.schema()["properties"]["valueString"]["title"]
    )
)


Map(
    source=Source(
        name='demographic.submitter_id',
        description=data_dict["clinical"]["demographic"]["properties"]["submitter_id"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["submitter_id"]["type"]
    ),
    destination=Destination(
        name='Patient.id',
        description=Patient.schema()["properties"]["id"]["description"],
        module='Administration',
        title=Patient.schema()["properties"]["id"]["title"],
        type=Patient.schema()["properties"]["id"]["type"]
    )
)


Map(
    source=Source(
        name='demographic.updated_datetime',
        description=data_dict["clinical"]["demographic"]["properties"]["updated_datetime"]["common"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["updated_datetime"]["oneOf"][0]["type"]
    ),
    destination=Destination(
        name='Extension.valueDateTime',
        description=Extension.schema()["properties"]["valueDateTime"]["description"],
        description_url='https://build.fhir.org/datatypes.html#dateTime',
        module='Extensibility',
        title=Extension.schema()["properties"]["valueDateTime"]["title"],
        type=Extension.schema()["properties"]["valueDateTime"]["type"]
    )
)


Map(
    source=Source(
        name='demographic.year_of_birth',
        description=data_dict["clinical"]["demographic"]["properties"]["year_of_birth"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["year_of_birth"]["oneOf"][0]["type"]

    ),
    destination=Destination(
        name='Patient.birthDate',
        description=Patient.schema()["properties"]["birthDate"]["title"],
        module='Administration',
        title=Patient.schema()["properties"]["birthDate"]["title"],
        type=Patient.schema()["properties"]["birthDate"]["type"],
        format=str(LiteralString)
    )
)


Map(
    source=Source(
        name='demographic.year_of_death',
        description=data_dict["clinical"]["demographic"]["properties"]["year_of_death"]["description"],
        category=data_dict["clinical"]["demographic"]["category"],
        type=data_dict["clinical"]["demographic"]["properties"]["year_of_death"]["type"]
    ),
    destination=Destination(
        name='Patient.deceasedDateTime',
        description=Patient.schema()["properties"]["deceasedDateTime"]["title"],
        module='Administration',
        title=Patient.schema()["properties"]["deceasedDateTime"]["title"],
        type=Patient.schema()["properties"]["deceasedDateTime"]["type"],
        format=str(LiteralString)
    )
)


Map(
    source=Source(
        name='diagnoses.age_at_diagnosis',
        description=data_dict["clinical"]["diagnosis"]["properties"]["age_at_diagnosis"]["description"],
        category=data_dict["clinical"]["diagnosis"]["category"],
        type=data_dict["clinical"]["diagnosis"]["properties"]["age_at_diagnosis"]["oneOf"][0]["type"]
    ),
    destination=Destination(
        name='Condition.onsetAge',
        description=Condition.schema()["properties"]["onsetAge"]["title"],
        module='Clinical Summary',
        title=Condition.schema()["properties"]["onsetAge"]["title"],
        type=Condition.schema()["properties"]["onsetAge"]["type"],
        format=''
    )
)