import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    user=os.getenv('POSTGRES_USER')
    password=os.getenv('POSTGRES_PASSWORD')
    db=os.getenv('POSTGRES_DB')
    host='localhost'
    port='5433'
    connection_str = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(connection_str)