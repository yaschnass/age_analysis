import requests
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import pandas as pd

# Define the base class for SQLAlchemy models
Base = declarative_base()

# Define table structure
class DataTable(Base):
    __tablename__ = 'data_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    party = Column(String)
    gender = Column(String)
    age = Column(Integer)

# Function to fetch senator data
def fetch_senator_data(url):
    response = requests.get(url)
    return response.json()

# Function to calculate age from birthday
def calculate_age(birthday_str):
    birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
    today = datetime.today().date()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

# Set up database and table
def setup_database():
    engine = create_engine('sqlite:///age_of_senators.db')
    Base.metadata.create_all(engine)
    return engine

# Function to insert data into the database
def insert_data_into_db(url):
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()

    # Fetch data and insert into the database
    data = fetch_senator_data(url)
    for item in data['objects']:
        age = calculate_age(item['person']['birthday'])
        record = DataTable(
            party=item['party'],
            gender=item['person']['gender'],
            age=age
        )
        session.add(record)
    session.commit()
    return engine

# Function to execute SQL query and return DataFrame
def get_average_age(engine):
    query = """
    SELECT party,
           gender,
           AVG(age) AS average_age
    FROM data_table
    WHERE gender IN ('male', 'female')
    GROUP BY party, gender
    ORDER BY party;
    """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df_average_age = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df_average_age

import matplotlib.pyplot as plt

def plot(df):
    # Pivot the DataFrame to have gender as columns
    df_pivot = df.pivot(index='party', columns='gender', values='average_age')
    # Plotting
    plt.figure(figsize=(10, 6))
    df_pivot.plot(kind='bar', figsize=(12, 8), colormap='viridis')
    plt.title('Average Age of Senators by Party and Gender')
    plt.xlabel('Party')
    plt.ylabel('Average Age')
    plt.xticks(rotation=45)
    plt.legend(title='Gender')
    plt.tight_layout()
    plt.show()

# Main function to run the script
def main():
    url = 'https://www.govtrack.us/api/v2/role?current=true&role_type=senator'
    engine = insert_data_into_db(url)
    df_average_age = get_average_age(engine)
    print(df_average_age)
    plot(get_average_age(engine))

if __name__ == "__main__":
    main()

   