import psycopg2
import re # used to get the deck_id from the filename
import boto3
import os
from os import listdir # used for looping through all the files in a directory

dbname = os.environ['CAPSTONE_DB_DBNAME']
host = os.environ['CAPSTONE_DB_HOST']
username = os.environ['CAPSTONE_DB_USERNAME']

conn = psycopg2.connect('dbname={} host={} user={}'.format(dbname, host, username))
cursor = conn.cursor()

def format_deck(raw_deck_list):
    """
    Takes a raw deck list and returns a nicely formatted deck list.

    INPUT:
        - raw_deck_list: String, unformatted deck list read directly from a file

    OUTPUT:
        - deck_list: list of strings, a formatted deck list ready for processing
    """
    deck_list = []
    for row in raw_deck_list.split('\r\n'):
        print(row)
        if row.startswith('S'):
            break
        deck_list.append(row)

    return deck_list

def parse_card_string(card_string):
    """
    Parses a single row of a deck list.

    INPUT:
        - card_string: a string of a row of the deck list

    OUTPUT:
        - card_name: a string of the name of the card
        - card_count: an int of the number of this card in the deck
    """
    card_count = int(card_string[0])
    card_name = card_string[2:]

    return card_name, card_count

def make_user_card_counts(deck_id, deck_list):
    """
    Takes a deck_id and deck_list and returns user-card-count tuples.

    INPUT:
        - deck_id: the unique identifier for the deck
        - deck_list: the deck list read from a file, formatted
    OUTPUT:
        - user_card_count: a tuple containing the deck_id, card_name and
                           card_count for each card in the deck.
    """

    user_card_count = []
    for card_string in deck_list:
        # hit the sideboard, done
        if card_string[0] == 'S':
            break
        card_name, card_count = parse_card_string(card_string)

        user_card_count.append((deck_id, card_name, card_count))

    return user_card_count

def read_deck_list(filepath):
    """
    Takes a filepath and reads the contents of the raw deck list stored there.

    INPUT:
        - filepath: string, the full path of the requested file,
                    i.e, 'data/raw_deck_lists/deck_list_371829'

    OUTPUT:
        - raw_deck_list: string, the un-formatted deck list read from the file
    """
    s3 = boto3.client('s3')
    bucketname = 'mtg-capstone'

    response = s3.get_object(Bucket=bucketname, Key=filepath)
    raw_deck_list = response['Body'].read().decode()

    return raw_deck_list

def add_item_db(user_card_count):
    """
    Adds a user_card_count item to the Postgres database.

    INPUT:
        - user_card_count: a tuple to be inserted into the db.

    OUTPUT:
        NONE

    """

    query = """INSERT INTO user_card_counts (user_id, card_name, card_count)
               VALUES ({user_id}, '{card_name}', {card_count})
            """.format(user_id=user_card_count[0], card_name=user_card_count[1],
                       card_count=user_card_count[2])

    cursor.execute(query)

    conn.commit()

def get_deck_id(filepath):
    """
    Gets the deck id from the end of the filepath string.
    """

    return int(re.search('deck_list_(\d+).txt', deck_file).group(1))

if __name__ == '__main__':
    path = '/Users/benjaminwalzer/Documents/Galvanize/mtg-capstone/data/raw_deck_lists/'

    for deck_file in listdir(path):
        deck_id = int(re.search('deck_list_(\d+).txt', deck_file).group(1))
        with open(path + deck_file, 'r') as f:
            deck_list = f.read()
            for item in make_user_card_counts(deck_id, deck_list):
                print(item)
