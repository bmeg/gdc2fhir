

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

    def update_mappings(self, name, mapping_key="source", new_values=None):
        """
        Updates values of source or destination keys

        :param schema: Json schema to be updated
        :param name: name of source or destination dictionary to be updated
        :param mapping_key: source of destination
        :param new_values: Dictionary with key and values to be updated
        :return: updated schema
        """
        for i, mapping_dict in enumerate(self.mappings):
            for key in mapping_dict:
                if key in mapping_key:
                    if mapping_dict[key]['name'] == name:
                        mapping_dict[key].update(new_values)
        return self

