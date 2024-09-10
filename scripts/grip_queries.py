
import pandas as pd
import sys
import gripql

conn = gripql.Connection("http://localhost:8201")
G=conn.graph("aced")


# Patient observations - test  --------------------
G.query().V().hasLabel("Patient").as_("patient").in_("focus_Patient").unwind("$.category").unwind("$.category.coding").has(gripql.eq("$.category.coding.code", "social-history")).execute()
patient_observation = G.query().V().hasLabel("Patient").as_("patient").in_("focus_Patient").unwind("$.code.coding").pivot("$patient._gid", "$.code.coding.system", "$.code.coding.display").execute()
patient_observation_df = pd.DataFrame(patient_observation)

# list the outgoing edges ---------------------------
outgoing_edges = []
for row in G.query().V().hasLabel('Patient').outE().execute():
    outgoing_edges.append(row['label'])
set(outgoing_edges)

# list the incoming edges ---------------------------
incoming_edges = []
for row in G.query().V().hasLabel('Patient').inE().execute():
    incoming_edges.append(row['label'])
set(incoming_edges)


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
