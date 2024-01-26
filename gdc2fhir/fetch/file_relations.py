from fhir.resources.documentreference import DocumentReference
from fhir.resources.attachment import Attachment


# file
DocumentReference.schema()['properties']
Attachment.schema()['properties']['title']['title']
Attachment.schema()['properties']['size']['title']
Extension.schema()['properties']['valueString']

