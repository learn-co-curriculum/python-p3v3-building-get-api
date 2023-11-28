# server/models.py

from enum import StrEnum, auto

class Division(StrEnum):
    Pacific = auto()    # "pacific"
    Central = auto()    # "central"
    Atlantic = auto()   # "atlantic"

class Team:
    all = {}  # dictionary with id as key

    def __init__(self, name, wins, losses, division):
        self.id = len(type(self).all.keys())+1
        self.name = name
        self.wins = wins
        self.losses = losses
        self.division = division
        type(self).all[self.id] = self
        
    @classmethod
    def seed(cls):
        """Initialize the dictionary with sample data"""
        Team(name="San Jose Swifts", wins=10, losses=2, division=Division.Pacific)
        Team(name="Chicago Chickadees", wins=7, losses=1, division=Division.Central)
        Team(name="Boston Buffleheads", wins=8, losses=3, division=Division.Atlantic)
