# gdc2fhir
![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)

## Project overview: 
Mapping GDC (Genomic Data Commons) schema to Ellrot's lab FHIR (Fast Healthcare Interoperability Resources) schema.

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
gdc2fhir/
|-- gdc2fhir/
|   |-- __init__.py
|   |-- labels/
|   |   |-- __init__.py
|   |   └── project.py
|   |-- schema.py
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
|   |-- __init__.py
|   └── test_mapping.py
|   |-- integration/
|   |-- __init__.py
|   └── test_schema.py
|   
|--README.md
└── setup.py
```

## Installation

- from source 
```
git clone repo
cd gdc2fhir
# create virtual env ex. 
python -m venv venv-gdc2fhir
source venv-gdc2fhir/bin/activate
python setup.py install
```

### Convert and Generate
 
- convert GDC schema keys to fhir mapping
- generate fhir object models ndjson files in directory

  Example run - replace path's to ndjson files or directories. 
 
```
gdc2fhir convert --name project --in_path projects.ndjson --out_path project_key.ndjson --verbose True

gdc2fhir generate --entity project --out_dir ./data --projects_path project_key.ndjson

``` 

### click cmds for constructing maps

initialize initial structure of project, case, or file to add Maps

```
gdc2fhir project_init 
gdc2fhir case_init 
gdc2fhir file_init 
# run ex. ./labels/project.py 
```


### Testing 
```
pytest -cov 
```
