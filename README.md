# fhirizer
![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)

## Project overview: 
Mapping GDC (Genomic Data Commons) schema or Cellosaurus cell-lines to FHIR (Fast Healthcare Interoperability Resources) schema.

### High-level mapping:
- #### GDC schema 
![mapping](./imgs/high-level.png)

- #### FHIR simplified schema 
![mapping](./imgs/gdc-fhir.png)


### gdc2fhir structure:

Data directories:
- **mapping**: json data maps done by gdc2fhir
- **resources**: data resources generated or used in mappings

****
```
fhirizer/
|-- fhirizer/
|   |-- __init__.py
|   |-- labels/
|   |   |-- __init__.py
|   |   |-- files.py
|   |   |-- case.py
|   |   └── project.py
|   |   
|   |-- schema.py
|   |-- entity2fhir.py
|   |-- mapping.py
|   |-- utils.py
|   └── cli.py
|   
|-- mapping/
|   |-- project.json
|   |-- case.json
|   └── file.json
|  
|-- resources/
|   |-- gdc_resources/
|   |   |-- content_annotations/
|   |   |-- data_dictionary/
|   |   └── fields/
|   └── fhir_resources/
| 
|-- tests/
|   |-- __init__.py
|   |-- unit/
|   |   |-- __init__.py
|   |   └── test_mapping.py
|   |-- integration/
|   |   |-- __init__.py
|   |   └── test_schema.py
|   └── fixtures/
|   
|--README.md
└── setup.py
```

## Installation

- from source 
```
git clone repo
cd fhirizer
# create virtual env ex. 
python -m venv venv-gdc2fhir
source venv-fhirizer/bin/activate
pip install . 
```

### Convert and Generate
 
- convert GDC schema keys to fhir mapping
- generate fhir object models ndjson files in directory

  Example run for patient - replace path's to ndjson files or directories. 
 
```
fhirizer convert --name case --in_path cases.ndjson --out_path cases_key.ndjson --verbose True

fhirizer generate --name case --out_dir ./data --entity_path cases_key.ndjson

``` 

- to generate document reference for the patients 

 
```
fhirizer convert --name file --in_path files.ndjson --out_path files_key.ndjson --verbose True

fhirizer generate --name file --out_dir ./data --entity_path files_key.ndjson

``` 

### click cmds for constructing maps

initialize initial structure of project, case, or file to add Maps

```
fhirizer project_init 
fhirizer case_init 
fhirizer file_init 
# run ex. ./labels/project.py 
```


### Testing 
```
pytest -cov 
```
