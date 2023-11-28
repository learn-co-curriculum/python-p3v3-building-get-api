# server/schemas.py

from marshmallow import Schema, fields
from models import Team

class TeamSchema(Schema):
    __model__ = Team
    id = fields.Int()
    name = fields.Str()
    wins = fields.Int()
    losses = fields.Int()
    division = fields.Str() 
