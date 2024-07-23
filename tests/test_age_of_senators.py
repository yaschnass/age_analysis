# age_of_senators.py (example implementation)
from datetime import datetime
import pandas as pd
import requests
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class DataTable(Base):
    __tablename__ = 'data_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    party = Column(String)
    gender = Column(String)
    age = Column(Integer)

def fetch_senator_data(url):
    response = requests.get(url)
    return response.json()

def calculate_age(birthday_str):
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d")
    today = datetime.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

# test_age_of_senators.py (your test file)
import pytest
from unittest.mock import patch
from age_of_senators import fetch_senator_data, calculate_age, DataTable

@pytest.fixture
def mock_data():
    return {
        "objects": [
            {"party": "Democratic", "person": {"birthday": "1975-01-01", "gender": "male"}},
            {"party": "Republican", "person": {"birthday": "1980-05-12", "gender": "female"}}
        ]
    }

@pytest.fixture
def db_setup():
    engine = create_engine('sqlite:///:memory:')  # In-memory database
    Base = declarative_base()

    class DataTable(Base):
        __tablename__ = 'data_table'
        id = Column(Integer, primary_key=True, autoincrement=True)
        party = Column(String)
        gender = Column(String)
        age = Column(Integer)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session, engine, Base
    
    Base.metadata.drop_all(engine)

def test_fetch_senator_data(mock_data):
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_data
        url = 'https://www.govtrack.us/api/v2/role?current=true&role_type=senator'
        data = fetch_senator_data(url)
        assert data == mock_data
        mock_get.assert_called_once_with(url)

def test_calculate_age():
    birthday = "2000-01-01"
    expected_age = datetime.today().year - 2000
    assert calculate_age(birthday) == expected_age

def test_database_insert(db_setup, mock_data):
    session, engine, Base = db_setup
    
    # Insert data into the in-memory database
    for item in mock_data['objects']:
        age = calculate_age(item['person']['birthday'])
        record = DataTable(
            party=item['party'],
            gender=item['person']['gender'],
            age=age
        )
        session.add(record)
    session.commit()

    # Query the database to ensure data is inserted correctly
    results = session.query(DataTable).all()
    assert len(results) == 2
    assert results[0].party == "Democratic"
    assert results[1].party == "Republican"
    assert results[0].age == calculate_age("1975-01-01")
    assert results[1].age == calculate_age("1980-05-12")
