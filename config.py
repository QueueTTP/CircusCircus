"""
Flask configuration variables.
"""
from os import environ, path

basedir = path.abspath(path.dirname(__file__))
# load_dotenv(path.join(basedir, '.env'))

class Config:
    """Set Flask configuration from .env file."""
    # General Config
    SECRET_KEY = 'kristofer'
    FLASK_APP = 'forum.app'

    # Database
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/circuscircus'
    
    #'sqlite:///circuscircus.db'

    #mysql database switched from 
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False