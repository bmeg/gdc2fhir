from fhir.resources.documentreference import DocumentReference
from fhir.resources.attachment import Attachment
from fhir.resources.extension import Extension


# file
DocumentReference.schema()['properties']
Attachment.schema()['properties']['title']['title']
Attachment.schema()['properties']['size']['title']
Extension.schema()['properties']['valueString']

