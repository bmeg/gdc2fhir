
import pandas as pd
import sys
import gripql

conn = gripql.Connection("http://localhost:8201")
G = conn.graph("aced")


# Patient observations - test  --------------------
G.query().V().hasLabel("Patient").as_("patient").in_("focus_Patient").unwind("$.category").unwind("$.category.coding").has(gripql.eq("$.category.coding.code", "social-history")).execute()
patient_observation = G.query().V().hasLabel("Patient").as_("patient").in_("focus_Patient").unwind("$.code.coding").pivot("$patient._gid", "$.code.coding.system", "$.code.coding.display").execute()
patient_observation_df = pd.DataFrame(patient_observation)


def edge_set(graph, direction) -> set:
    """Fetches set of edges to graph node/vertex based on direction in/out"""
    edges = []
    edge_set = None

    if direction in "out":
        for row in graph.outE().execute():
            edges.append(row['label'])
        edge_set = set(edges)
    elif direction in "in":
        for row in graph.inE().execute():
            edges.append(row['label'])
        edge_set = set(edges)

    if edge_set:
        return edge_set

# list the outgoing edges ---------------------------
patient_out_edges = edge_set(graph=G.query().V().hasLabel('Patient'), direction="out")

# list the incoming edges ---------------------------
patient_in_edges = edge_set(graph=G.query().V().hasLabel('Patient'), direction="in")


# Patient - demographics ------------------------------
# race and ethnicity - GDC and ombCategory (less complete)
race_ethnicity = G.query().V().hasLabel('Patient').as_("patient").unwind("extension").unwind("extension.extension").pivot("$patient._gid", "$.extension.extension.valueCoding.system", "$.extension.extension.valueCoding.display").execute()
race_ethnicity_df = pd.DataFrame(race_ethnicity)

# race - FHIR standard (more complete)
fhir_race = G.query().V().hasLabel('Patient').as_("patient").unwind("extension").has(gripql.eq("extension.url", "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race")).pivot("$patient._gid", "$.extension.url", "$.extension.valueString").execute()
fhir_race_df = pd.DataFrame(fhir_race)

# ethnicity - FHIR standard (more complete)
fhir_ethnicity = G.query().V().hasLabel('Patient').as_("patient").unwind("extension").has(gripql.eq("extension.url", "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity")).pivot("$patient._gid", "$.extension.url", "$.extension.valueString").execute()
fhir_ethnicity_df = pd.DataFrame(fhir_ethnicity)

# bith sex
birth_sex = G.query().V().hasLabel('Patient').as_("patient").unwind("extension").has(gripql.eq("extension.url", "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex")).pivot("$patient._gid", "$.extension.url", "$.extension.valueCode").execute()
birth_sex_df = pd.DataFrame(birth_sex)

# age
age = G.query().V().hasLabel('Patient').as_("patient").unwind("extension").has(gripql.eq("extension.url", "http://hl7.org/fhir/SearchParameter/patient-extensions-Patient-age")).pivot("$patient._gid", "$.extension.url", "$.extension.valueQuantity.value").execute()
age_df = pd.DataFrame(age)

# deseased dateTime
G.query().V().hasLabel('Patient').as_("patient").fields("$.deceasedDateTime").execute()

# social history - smoking
pack_year = G.query().V().hasLabel("Patient").as_("patient").in_("focus_Patient").unwind("$.category").unwind("$.category.coding").has(gripql.eq("$.category.coding.code", "social-history")).unwind("$.code.coding").has(gripql.eq("$.code.coding.code", "8664-5")).pivot("$patient._gid", "$.code.coding.display", "$.valueQuantity.value").execute()
per_day = G.query().V().hasLabel("Patient").as_("patient").in_("focus_Patient").unwind("$.category").unwind("$.category.coding").has(gripql.eq("$.category.coding.code", "social-history")).unwind("$.code.coding").has(gripql.eq("$.code.coding.code", "64218-1")).pivot("$patient._gid", "$.code.coding.display", "$.valueQuantity.value").execute()
pack_year_df = pd.DataFrame(pack_year)
per_day_df = pd.DataFrame(per_day)

# social history - alcohol use
alcohol = G.query().V().hasLabel("Patient").as_("patient").in_("focus_Patient").unwind("$.category").unwind("$.category.coding").has(gripql.eq("$.category.coding.code", "social-history")).unwind("$.code.coding").has(gripql.eq("$.code.coding.code", "11331-6")).pivot("$patient._gid", "$.code.coding.display", "$.valueString").execute()
alcohol_df = pd.DataFrame(alcohol)

# Patient - condition  ------------------------------
# Patient primary diagnosis
primary_diagnosis = G.query().V().hasLabel("Patient").as_("patient").in_("focus_Patient").unwind("$.category").unwind("$.category.coding").has(gripql.eq("$.category.coding.code", "exam")).unwind("$.code.coding").pivot("$patient._gid", "$.code.coding.system", "$.code.coding.display").execute()
primary_diagnosis_df = pd.DataFrame(primary_diagnosis)

# Patient primary site
primary_site = G.query().V().hasLabel("Patient").as_("patient").out("body_structure").unwind("$.includedStructure").unwind("$.includedStructure.structure.coding").pivot("$patient._gid", "$.includedStructure.structure.coding.system", "$.includedStructure.structure.coding.display").execute()
primary_site_df = pd.DataFrame(primary_site)

# Patient cancer stage TODO: Need to fetch from observation to create one column per stage classification
stage = G.query().V().hasLabel("Patient").as_("patient").out("condition").unwind("$.stage").unwind("$.stage.type.coding").has(gripql.eq("$.stage.type.coding.system" ,"https://cadsr.cancer.gov/")).unwind("$.stage.summary.coding").has(gripql.eq("$.stage.summary.coding.system", "https://ncit.nci.nih.gov")).pivot("$patient._gid", "$.stage.type.coding.display", "$.stage.summary.coding.display").execute()
stage_df = pd.DataFrame(stage)

# Document Reference ---------------------
file = G.query().V().hasLabel("DocumentReference").execute()
file_type = G.query().V().hasLabel("Patient").as_("patient").out("document_reference").unwind("$.type.coding").pivot("$patient._gid", "$.type.coding.display", "$.type.coding.display").execute()
file_type_df = pd.DataFrame(file_type)

# list the outgoing edges ---------------------------
file_out_edges = edge_set(graph=G.query().V().hasLabel("DocumentReference"), direction="out")

# list the incoming edges ---------------------------
file_in_edges = edge_set(graph=G.query().V().hasLabel("DocumentReference"), direction="in")

# seperate value[x] boolean, string, integer, quantity, dateTime file observation components
# in this case the df complement each-other. overlap will fill columns that are missing all cells if value[x] exists
file_component_valuestring = G.query().V().hasLabel("DocumentReference").as_("document").in_("focus_DocumentReference").unwind("$.component").unwind("$.component.code.coding").pivot("$document._gid", "$.component.code.coding.code", "$.component.valueString").execute()
file_component_valuequantity = G.query().V().hasLabel("DocumentReference").as_("document").in_("focus_DocumentReference").unwind("$.component").unwind("$.component.code.coding").pivot("$document._gid", "$.component.code.coding.code", "$.component.valueQuantity").execute()
# file_component_valueinteger = G.query().V().hasLabel("DocumentReference").as_("document").in_("focus_DocumentReference").unwind("$.component").unwind("$.component.code.coding").pivot("$document._gid", "$.component.code.coding.code", "$.component.valueInteger").execute()
# file_component_valuedatetime = G.query().V().hasLabel("DocumentReference").as_("document").in_("focus_DocumentReference").unwind("$.component").unwind("$.component.code.coding").pivot("$document._gid", "$.component.code.coding.code", "$.component.valueDateTime").execute()

file_component_valuestring_df = pd.DataFrame(file_component_valuestring)
file_component_valuequantity_df = pd.DataFrame(file_component_valuequantity)