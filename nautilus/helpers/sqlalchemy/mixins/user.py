"""
    This file defines the models used by the user service.
"""

# third party imports
from sqlalchemy import Column, Text
from .hasID import HasID


class User(HasID):
    """ The user model used by Synca. """
    firstName = Column(Text)
    lastName = Column(Text)
    email = Column(Text)
    username = Column(Text)
