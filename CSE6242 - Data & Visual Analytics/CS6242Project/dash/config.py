import os
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', '26EB75AC122AA66A8734DB30BF334955972FA0D4')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql+psycopg2://crsp:crspcse6242@database-1.cudz1l7w5ie2.us-east-1.rds.amazonaws.com:5432/crsp')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
