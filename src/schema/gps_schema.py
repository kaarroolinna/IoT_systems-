from marshmallow import Schema, fields

class GpsSchema(Schema):
    longitude = fields.Float(required=True)
    latitude = fields.Float(required=True)