import json
import pandas as pd
import plotly.express as px

file_path = "META/DocumentReference.ndjson"


def read_ndjson(file_path):
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]


def extract_category(ndjson_data):
    dat = []
    for entry in ndjson_data:
        if entry.get("resourceType") == "DocumentReference":
            _entry = {
                coding.get("system", ""): coding.get("display", "")
                for category in entry.get("category", [])
                for coding in category.get("coding", [])
            }
            dat.append(_entry)
    return pd.DataFrame(dat)


files = read_ndjson(file_path)
category_data_pivot = extract_category(files)
category_data_pivot.rename(columns={"https://gdc.cancer.gov/data_category": "Data Category", "https://gdc.cancer.gov/experimental_strategy" : "Experimental Strategy", "https://gdc.cancer.gov/platform": "Platform", "https://gdc.cancer.gov/wgs_coverage": "WGS Coverage"} , inplace=True)


def file_category_barchart(df, column_name, output_file):
    value_counts = df[column_name].value_counts().reset_index()
    value_counts.columns = [column_name, 'Count']
    # fig = px.bar(value_counts, x=column_name, y='Count', title=f'{column_name}', color='Count', color_continuous_scale=['#32a852', '#3261a8', '#a83259'])
    fig = px.bar(value_counts, x=column_name, y='Count', title=f'{column_name}', color_discrete_sequence=['#4ca7ce'])
    fig.write_image(output_file)


for column in category_data_pivot.columns:
    output_file = f"plots/{"_".join(column.split('/')[-1].split(" "))}_barchart.png"  
    file_category_barchart(category_data_pivot, column, output_file)


def file_category_piechart(df, column_name, output_file):
    value_counts = df[column_name].value_counts().reset_index()
    value_counts.columns = [column_name, 'Count']
    fig = px.pie(value_counts, names=column_name, values='Count', title=f'{column_name}')
    fig.write_image(output_file)


for column in category_data_pivot.columns:
    output_file = f"plots/{'_'.join(column.split(' '))}_piechart.png"  
    file_category_piechart(category_data_pivot, column, output_file)

category_data_pivot.to_csv("plots/output_file_category.csv", index=False)
