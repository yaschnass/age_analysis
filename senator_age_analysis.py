import requests
import json
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker
import pandas as pd

# Download JSON
url = 'https://www.govtrack.us/api/v2/role?current=true&role_type=senator'
response = requests.get(url)
data = response.json()

# Set up  database 
engine = create_engine('sqlite:///age_of_senators.db')
Base = declarative_base()

# Define table structure
class DataTable(Base):
    __tablename__ = 'data_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    party = Column(String)
    gender = Column(String)
    age = Column(Integer)

# Create table
Base.metadata.create_all(engine)

# Insert data into the table
Session = sessionmaker(bind=engine)
session = Session()

from datetime import datetime

# Function to calculate age from birthday
def calculate_age(birthday_str):
    birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
    today = datetime.today().date()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

# Create DataTable record with the party, gender, and calculated age
for item in data['objects']:
    age = calculate_age(item['person']['birthday'])
    record = DataTable(
        party=item['party'],
        gender=item['person']['gender'],
        age=age
    )
    session.add(record)

# Commit the transaction
session.commit()

print("Data has been inserted successfully.")

# Define SQL query to calculate average age by gender and party
query = """
SELECT party,
       gender,
       AVG(age) AS average_age
FROM data_table
WHERE gender IN ('male', 'female')
GROUP BY party, gender
ORDER BY party ;
"""

# Execute the query and fetch results into Pandas DataFrame
with engine.connect() as conn:
    result = conn.execute(text(query))
    df_average_age = pd.DataFrame(result.fetchall(), columns=result.keys())

# Display the DataFrame
print(df_average_age)

import matplotlib.pyplot as plt


# Pivot the DataFrame to have gender as columns
df_pivot = df_average_age.pivot(index='party', columns='gender', values='average_age')
