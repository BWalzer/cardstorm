import requests
import re
import json
import random
import time
import boto3
from bs4 import BeautifulSoup
import psycopg2
import os
from os import listdir # used for looping through all the files in a directory

s3 = boto3.client('s3')

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


################################################################################
############## Above functions from make_user_card_counts.py ###################
################################################################################

def get_event_ids(front_page, verbose=False):
    """
    Takes in a front page of mtgtop8.com and returns a list of
        the event ids

    INPUT:
        - front_page: a BeautifulSoup object of the front page

    OUTPUT:
        - event_ids: a list of all the event ids from the 'Last 10 Events' table
    """

    if verbose: print('\tGetting event ids from a front page')

    event_list = [event['href'] for event in front_page.find_all('table')[2]
         .find('td').find_next_sibling().find_all('table')[1].find_all('a')]

    # use map() and regular expressions to get the event id out of the anchor tags
    event_ids = list(map(lambda x: re.search("e=(\d+)&", x).group(1),
                                                        event_list))

    return event_ids

def get_deck_ids(event_page, verbose=False):
    """Takes in an event page and returns a list of all the deck ids on that page.

    INPUT:
        - event_page: BeautifulSoup objet of the event page from mtgtop8.com

    OUTPUT:
        - deck_ids: List of all deck ids on the page"""

    # Get to the table that contains the links to all the deck lists
    deck_list_table = event_page.find_all('table')[3].find_all('a')


    # deck_list_ids is a list of all the unique ids for the deck lists
    deck_ids = []

    # loop through each of the anchor tags in each of the deck list tables
    for anchor in deck_list_table:
        # find only anchors where 'e=' and 'd=' are in the href. This is only the actual deck lists
        if ('d=' in anchor['href'] and 'e=' in anchor['href']):
            # add the id to the list
            deck_ids.append(re.search('d=(\d+)&', anchor['href']).group(1))

    return deck_ids

def deck_request(deck_id, verbose=False):
    """Takes a deck_id and returns the response from the request. Errors will come later.

    INPUT:
        - deck_id: the unique id for the desired deck list from mtgtop8.com

    OUTPUT:
        - deck_list: a list of strings representing the deck list corresponding
                     to the deck_id."""

    if verbose: print('\t\tDeck request for deck id {}'.format(deck_id))

    # repeat this process a max of 5 times. If status_code==200, break
    for i in range(5):
        try:
            response = requests.get('http://mtgtop8.com/mtgo?d={}'.format(deck_id),
                                headers={'User-Agent': 'Getting some deck lists'})

            # if good status code, quit loop and return
            # otherwise, keep going for a max of 5 times
            if response.status_code == 200:
                break

            if verbose: print('bad status code: {}. try {} of 5'.format(response.status_code, i+1))

        except:
            print("Error connecting to http://mtgtop8.com/mtgo?d={}".format(deck_id))
        # preventing submitting too fast
        time.sleep(2 + random.random())


    deck_list = response.content

    return deck_list

def event_request(event_id, verbose=False):
    """Takes an event_id and returns the response from the request. Errors will come later.

    INPUT:
        - event_id: the unique id for the desired event from mtgtop8.com

    OUTPUT:
        - response: the response from the get request"""

    if verbose: print('\tEvent request for event id {}'.format(event_id))

    # repeat this process a max of 5 times. If status_code==200, break
    for i in range(5):
        try:
            response = requests.get('http://mtgtop8.com/event?e={}'.format(event_id),
                                headers={'User-Agent': 'Getting some event info'})

        # if good status code, quit loop and return
        # otherwise, keep going for a max of 5 times
        if response.status_code == 200:
            break
        if verbose: print('bad status code: {}. try {} of 5'.format(response.status_code, i+1))
        except:
            print("Error connecting to http://mtgtop8.com/event?e={}".format(event_id))

        # preventing submitting too fast
        time.sleep(2 + random.random())


    return response

def modern_front_page_request(page_number=0, verbose=False):
    """Sends a get request to mtgtop8.com with the given page number

    INPUT:
        - page_number: argument for the get request. page_number of 3 gets decks from 21-30.
                       Default value of 0 to get decks from 1-10.

    OUTPUT:
        - response: the response from the get request"""

    # repeat this process a max of 5 times. If status_code==200, break
    if verbose: print('Requesting front page number {}'.format(page_number))


    for i in range(5):
        try:
            response = requests.get('http://mtgtop8.com/format?f=MO&meta=44&cp={}'.format(page_number),
                                    headers={'User-Agent': 'Modern front page request'})
            # if good status code, quit loop and return
            # otherwise, keep going for a max of 5 times
            if response.status_code == 200:
                break

            if verbose: print('bad status code: {}. try {} of 5'.format(response.status_code, i+1))

        except:
            print("Error connecting to http://mtgtop8.com/format?f=MO&meta=44&cp={}".format(page_number))

        time.sleep(2 + random.random())

    return response

def get_deck_lists(event_ids, verbose=False):
    """
    Takes a list of event ids, sends get requests to mtgtop8.com for each event
        id and pulls the deck ids from the event page. Once it has all the deck
        ids from each event page, a dictionary of deck lists is compiled and
        returned.

    INPUT:
        - event_ids: a list of unique event ids for the desired events from
                     mtgtop8.com

    OUTPUT:
        - deck_lsits: a dictionary of deck lists, with key=deck_id and
                      value=deck_list.

    """

    deck_ids = set()
    for event_id in event_ids:


        # send a get request to for the event page, and load it into a BS
        event_page = BeautifulSoup(event_request(event_id).text, 'html.parser',
                                                            verbose=verbose)

        # update the set of deck ids with result from get_deck_ids()
        deck_ids.update(get_deck_ids(event_page, verbose=verbose))

    # get a deck list for each deck id, in a dictionary with key=deck_id and
    # value=deck list
    deck_lists = deck_requests(deck_ids, verbose=verbose)

    return deck_lists

def save_decklists(deck_id, deck_list, verbose=False):
    """
    Saves a deck list as a text file in my s3 bucket.

    INPUT:
        - deck_id: the unique id for the deck list
        - deck_list: the deck list to be saved in the s3 bucket.

    OUTPUT:
        NONE
    """

    bucketname = 'mtg-capstone'
    filename = 'data/raw_deck_lists/deck_list_{}.txt'.format(deck_id)

    s3.put_object(Bucket=bucketname, Key=filename, Body=deck_list)

def scrape_decklists(scraped_events, front_pages=[0], verbose=False):
    """
    Version 2. Scrapes mtgtop8.com for modern deck lists.

    INPUT:
        - front_pages: list of integers for each front page to request. Each
                       value in the list will get 10 events. Default value: [0]
        - scraped_events: a set of all previously scraped event_ids. These
                          event_ids will not be re-scraped.
        - verbose: boolean indicating if status messages are printed to the
                   console. Default value: False
    OUTPUT:
        - scraped_events: a set of event_ids which have been scraped. updated.
    """

    for page_number in front_pages:
        front_page = modern_front_page_request(
                                       page_number=page_number, verbose=verbose)
        front_page_soup = BeautifulSoup(front_page.text, 'html.parser')
        event_ids = get_event_ids(front_page=front_page_soup,
                                                verbose=verbose)

        for event_id in event_ids:
            if event_id in scraped_events:
                if verbose: print('\t\tevent id {} already scraped'.format(event_id))
                continue
            event_page = event_request(event_id=event_id,
                                                    verbose=verbose)
            event_page_soup = BeautifulSoup(event_page.text, 'html.parser')
            deck_ids = get_deck_ids(event_page=event_page_soup,
                                                  verbose=verbose)
            for deck_id in deck_ids:
                deck_list = deck_request(deck_id=deck_id,
                                                       verbose=verbose)
                save_decklists(deck_id, deck_list, verbose=verbose)

            scraped_events.add(event_id)

    return scraped_events

def scrape_decklists_2(scraped_events, front_pages=[0], verbose=False):
    '''

    Front page request
        get event ids
        for event ids:
            event request
            get deck ids
            for deck_ids:
                deck request
                make user-card-counts
                upload to db
    '''

    raw_front_page = modern_front_page_request(page_number=page_number, verbose=verbose)
    front_page = BeautifulSoup(raw_front_page.text, 'html.parser')

    event_ids = get_event_ids(front_page, verbose=verbose)

    for event_id in event_ids:
        if event_id in scraped_events:
            if verbose: print('event id {} has already been scraped'.format(event_id))
            continue
        raw_event_page = event_request(event_id, verbose=verbose)
        event_page = BeautifulSoup(raw_event_page.text, 'html.parser')

        deck_ids = get_deck_ids(event_page, verbose=verbose)

        for deck_id in deck_ids:
            raw_deck_list = deck_request(deck_id, verbose=verbose)
            deck_list = format_deck(raw_deck_list)
            user_card_counts = make_user_card_counts(deck_id, deck_list)

            upload_user_card_counts(user_card_counts)

if __name__ == '__main__':
    response = s3.get_object(Bucket='mtg-capstone', Key='data/scraped_events.json')
    scraped_events = set(json.loads(response['Body'].read().decode()))
    print('Scraped event ids: {}'.format(scraped_events))

    updated_scraped_events = scrape_decklists(scraped_events=scraped_events,
                                              front_pages=range(100),
                                              verbose=True)

    print('Updated scraped event ids: {}'.format(updated_scraped_events))
    s3.put_object(Bucket='mtg-capstone', Key='data/scraped_events.json',
                  Value=json.dumps(list(updated_scraped_events)))