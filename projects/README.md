### Project Directory Overview
This directory serves as a placeholder for user input/output to the fhirizer client and may contain various GDC or Cellosaurus studies.
The META folder within each project's study folder contains the FHIR ndjson output data generated via fhirizer.


#### Data to convert:
##### - Genomics Data Commons (GDC)
Valid data input consists of ndjson files fetched via [GDC API query](https://docs.gdc.cancer.gov/API/Users_Guide/Python_Examples/) for each `case`, `file`, and `project` end points. 
an example script can be found here: https://github.com/bmeg/bmeg-etl/blob/develop/transform/gdc/gdc-scan.py 

A complete and unfiltered query of both `case` and `file` endpoints will contain the minimum viable information necessary for a comprehensive downstream analysis, including relational associations to `project` and `program` for each patient. Therefore, converting these two entities in separate steps will enable users to parse GDC data into FHIR semantic format effectively.
Below is an example of the data-schema conversion and generation flow for a single GDC study:

1. User input to fhirizer client: 
   - ./projects/TCGA-STUDY/cases.ndjson
   - ./projects/TCGA-STUDY/files.ndjson
2. Convertion of projects' study data.
   - Case
    ``` 
   fhirizer convert --name case --in_path ./projects/<my-study>/cases.ndjson --out_path ./projects/<my-study>/cases_key.ndjson 
   ```
   - File
    ``` 
   fhirizer convert --name file --in_path ./projects/<my-study>/files.ndjson --out_path ./projects/<my-study>/files_key.ndjson 
   ```
   
3. Generation of FHIR ndjson output stored in META folders.
   - Case
    ``` 
     fhirizer generate --name case --out_dir ./projects/<my-project>/META --entity_path ./projects/<my-project>/cases_key.ndjson
   ```
   - File
    ``` 
     fhirizer generate --name file --out_dir ./projects/<my-project>/META --entity_path ./projects/<my-project>/files_key.ndjson
   ```
4. Validate output:
    
    To validate the output data generated via fhirizer, you can run the following command provided by [g3t_etl](https://github.com/ACED-IDP/g3t_etl) in your study's directory:
    ```
    g3t utilities meta validate > out.txt
    ```
    This command will validate the output data in META folder and redirect the validation results to the out.txt file for further inspection. 

##### - Cellosaurus

- preprocessing 
  - The [Cellosaurus GET API](https://api.cellosaurus.org/) provides access to the purest data format available. Utilizing Cellosaurus's `fhirizer resource`, you can transform a subset of cell-lines, that have previously been filtered from cellosaurus.obo to cells.json.gz, into a refined cellosaurus ndjson file. This file can then be used with `fhirizer generate` to create Cellosaurus FHIR objects. 
  ```
   fhirizer resource --name cellosaurus --path tests/fixtures/cellosaurus/cells.json.gz  --out_dir tests/fixtures/cellosaurus
  ```

1. User input to fhirizer client: 
   - ./projects/cellosaurus-STUDY/cellosaurus_celllines.ndjson
2. Generation of FHIR ndjson output stored in META folders.
    ```
      fhirizer generate --name cellosaurus --out_dir ./projects/<my-study>/META --entity_path ./projects/<my-study>/cellosaurus-celllines.ndjson
    ```
3. Validate output:
   ```
    g3t meta validate
    ```