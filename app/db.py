import os
import pytz
import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Table

load_dotenv()
IST = pytz.timezone("Asia/Kolkata")
DATABASE_URL = os.environ.get("DATABASE_URL")

base = declarative_base()
engine = create_engine(DATABASE_URL)
connection = engine.connect()
metadata = MetaData()
Session = sessionmaker(bind=engine)
session = Session()
subscribe_table = Table(
    "subscribe",
    metadata,
    autoload=True,
    autoload_with=engine
)


def add_subscriber(number):
    current_time = datetime.datetime.now(IST)
    query = subscribe_table.insert().values(
        number=number,
        subscribe_time=current_time
    )
    result = connection.execute(query)


def remove_subscriber(number):
    query = subscribe_table.delete().where(subscribe_table.c.number == number)
    result = connection.execute(query)


def get_all_subscribers():
    query = subscribe_table.select()
    result = connection.execute(query).fetchall()
    result = [row[0] for row in result]
    return result


def get_expiring_subscribers():
    current_time = datetime.datetime.now(IST)
    query = subscribe_table.select().where(subscribe_table.c.subscribe_time <
                                           current_time - datetime.timedelta(hours=48))
    result = connection.execute(query).fetchall()
    if result:
        result = [row[0] for row in result]
    return result


def check_subscriber_exists(number):
    query = subscribe_table.select().where(subscribe_table.c.number == number)
    result = connection.execute(query).fetchall()
    return bool(result)
