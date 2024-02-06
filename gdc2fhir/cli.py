from gdc2fhir import utils, schema
import click


@click.group()
def cli():
    """GDC to FHIR Key and Content Mapping"""
    pass


@cli.command('fields')
@click.option('--input_path', required=True,
              default='./resources/gdc_resources/fields/case_fields.json',
              show_default=True,
              help='Path to available GDC field json files in this repo')
def field_keys(input_path):
    case_fields = utils.read_json(input_path)
    """
    # TODO just testing a place holder for future cli functions and calls
    schema_instance = schema.Schema(metadata={},
                                    obj_mapping=schema.Map(source=schema.Source(), destination=schema.Destination()),
                                    obj_key=case_fields, mappings=[])
    """
    print("reading from input_path: ", input_path)
    print("case fields: ", case_fields)
    # print("schema object: ", schema_instance)


if __name__ == '__main__':
    cli()

