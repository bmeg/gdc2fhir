

class Schema:
    def __init__(self, version, schema_standard: str, metadata: dict, obj_mapping: dict,
                 obj_keys: list, source_key_required: list, destination_key_required: list, unique_keys: list,
                 source_key_aliases: dict, mappings: list):
        self.version = version
        self.schema_standard = schema_standard
        self.metadata = metadata
        self.obj_mapping = obj_mapping
        self.obj_keys = obj_keys
        self.source_key_required = source_key_required
        self.destination_key_required = destination_key_required
        self.unique_keys = unique_keys
        self.source_key_aliases = source_key_aliases
        self.mappings = mappings

    def update_metadata(self, m):
        self.metadata.update(m)

    def filter_mappings(self, schema):
        pass

    def transition_mappings(self):
        pass

    def update_mappings(self, source_name, source=True, destination=False, source_values=None, destination_values=None):
        """
        Updates values of source and/or destination keys

        :param schema: Json schema to be updated
        :param source_name: name of source to be updated
        :param source: boolean indicating source to be updated
        :param destination: boolean indicating destination to be updated
        :param source_values: Dictionary with updated info
        :param destination_values: Dictionary with updated info
        :return: updated schema
        """
        for i, mapping_dict in enumerate(self.mappings):
            for key in mapping_dict:
                if key == "source" and source:
                    if mapping_dict[key]['name'] == source_name:
                        mapping_dict[key].update(source_values)
                        if destination:
                            mapping_dict['destination'].update(destination_values)
                            print(mapping_dict)

