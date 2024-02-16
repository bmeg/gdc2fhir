from fhir.resources.identifier import Identifier
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.researchstudy import ResearchStudyRecruitment
from fhir.resources.extension import Extension
from fhir.resources.reference import Reference
from fhir.resources.condition import Condition

identifier = Identifier.construct()
identifier.value = "TCGA-BRCA"

rs = ResearchStudy.construct()
rs.status = "open-released" # assign required fields first
rs.identifier = [identifier]
rs.name = "Breast Invasive Carcinoma"
rs.id = "phs000178"

cc = CodeableConcept.construct()
cc.coding = [{'system': "http://snomed.info/sct", 'code': "115219005", 'display': "Acinar Cell Neoplasms"}]
rs.condition = [cc, cc, cc, cc]

rs_parent = ResearchStudy.construct()
identifier_parent = Identifier.construct()
identifier_parent.value = "b80aa962-9650-5110-b3eb-bd087da808db"

rs_parent.status = "open" # assign required fields first
rs_parent.name = "TCGA"
rs_parent.identifier = [identifier_parent]

rsr = ResearchStudyRecruitment.construct()
rsr.actualNumber = 443
rs.recruitment = rsr

ref = Reference.construct()
ref.type = str(ResearchStudy)
ref.identifier = identifier_parent
rs.partOf = [ref]

e = Extension.construct()
e.valueUnsignedInt = 60945
rs.extension = [e]

#  condition -- subject --> patient <--subject-- researchsubject -- study --> researchstudy -- partOf --> researchstudy

rs.dict()

