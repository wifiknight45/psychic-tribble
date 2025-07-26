from marshmallow import Schema, fields, validate

class UserCreateSchema(Schema):
    name = fields.String(required=True)

class EventCreateSchema(Schema):
    name = fields.String(required=True)

class TimeslotCreateSchema(Schema):
    day = fields.String(required=True)
    start = fields.String(
        required=True,
        validate=validate.Regexp(r'^\d{2}:\d{2}$', error="HH:MM format")
    )
    end = fields.String(
        required=True,
        validate=validate.Regexp(r'^\d{2}:\d{2}$', error="HH:MM format")
    )

class AssignmentSchema(Schema):
    user_id = fields.String(required=True)
 
