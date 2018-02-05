import requests
import re
import numpy as np
import json
import random
import time
from bs4 import BeautifulSoup
import psycopg2
import os

dbname = os.environ['CAPSTONE_DB_DBNAME']
host = os.environ['CAPSTONE_DB_HOST']
username = os.environ['CAPSTONE_DB_USERNAME']
password = os.environ['CAPSTONE_DB_PASSWORD']

conn = psycopg2.connect('dbname={} host={} user={} password={}'.format(dbname, host, username, password))
cursor = conn.cursor()


class ReflexiveDict():

    def __init__(self):
        self._dict = {}
        self._get_cards()

    def __setitem__(self, key, val):
        self._dict[key] = val
        self._dict[val] = key

    def __getitem__(self, key):
        return self._dict[key]

    def keys(self):
        return self._dict.keys()

    def __contains__(self, key):
        return key in self._dict

    def _get_cards(self):
        query = 'Select name, cardstorm_id FROM cards'

        try:
            cursor.execute(query)

            for name, cardstorm_id in cursor.fetchall():
                self[name] = cardstorm_id
        except:
            return False

        return True

    def get_cardstorm_ids(self):
        all_cardstorm_ids = [key for key in self.keys() if isinstance(key, int)]

        return np.array(sorted(all_cardstorm_ids))

# dictionary of every modern legal card
card_dict = ReflexiveDict()

def format_deck(raw_deck_list):
    """
    Takes a raw deck list and returns a nicely formatted deck list.

    INPUT:
        - raw_deck_list: String, unformatted deck list read directly from a file

    OUTPUT:
        - deck_list: list of strings, a formatted deck list ready for processing
    """
    if not raw_deck_list: # deck list is empty, return []
        return []
    deck_list = []
    for row in raw_deck_list.split('\r\n'):
        if row.startswith('S') or not row:
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
    if card_string:
        count_search = re.search('(\d+)', card_string)
        if count_search: # card_count found
            card_count = count_search.group(1)
        else:
            card_count = 1

        card_name = re.search('(\D+)', card_string).group(1).strip()

        if ' / ' in card_name: # split cards. mtgtop8 formats these weirdly
            card_name = card_name.replace(' / ', ' // ')
        return True, card_name, card_count

    return False, None, None

def make_user_card_counts(event_id, deck_id, deck_list,verbose=False):
    """
    Takes a deck_id and deck_list and returns user-card-count tuples.

    INPUT:
        - event_id: the unique identifier for the event this deck came from
        - deck_id: the unique identifier for the deck
        - deck_list: the deck list read from a file, formatted
        # - cursor: psycopg2 cursor object, used to get cardstorm_id from db
        - verbose: bool, if true status messages will be printed
    OUTPUT:
        - user_card_count: a tuple containing the deck_id, card_name and
                           card_count for each card in the deck.
    """

    user_card_count = []
    for card_string in deck_list:
        parse_success, card_name, card_count = parse_card_string(card_string)
        cardstorm_id = get_cardstorm_id(card_name, verbose=verbose)
        if not cardstorm_id: # could not find cardstorm_id, most likely not a valid card
            continue
        if parse_success:
            user_card_count.append((int(event_id), int(deck_id), cardstorm_id, card_name, card_count))

    return user_card_count

def upload_user_card_counts(user_card_counts, verbose=False):
    '''
    Uploads a deck list, split into user_card_count pairs, to the PostreSQL database.

    INPUT:
        - user_card_count: list of tuples containing the user_card_counts for a deck list
        - cursor: cursor object, from the databse connection
        - verbose: bool, if True status statements are printed

    OUTPUT:
        - success: bool: True if user_card_counts was successfully uploaded to the database.
                         False if an exception was caught.
    '''

    template = ', '.join(['%s'] * len(user_card_counts))
    query = 'INSERT INTO decks (event_id, deck_id, cardstorm_id, card_name, card_count) VALUES {}'.format(template)

    try:
        cursor.execute(query=query, vars=user_card_counts)

    except psycopg2.IntegrityError:
        if verbose: print('            duplicate key: deck not added to db')
        return False

    return True

def get_cardstorm_id(card_name, verbose=False):
    '''
    Turns a card name into its' unique cardstorm id

    INPUT:
        - card_name: string, the name of a magic card
        - verbose: bool, if true status messages are printed. Default false.

    OUTPUT:
        - cardstorm_id: int, unique id for the card. If the card was not found,
                        0 is returned.
    '''

    if verbose: print('            {}'.format(card_name))
    try:
        cardstorm_id = card_dict[card_name.lower()]
    except KeyError:
        if verbose: print('            {} not found'.format(card_name))
        return 0

    return cardstorm_id

def get_scraped_deck_ids(verbose=False):
    '''
    Gets the deck_ids for all previously scraped decks.

    INPUT:
        - verbose: bool, if True prints status statements

    OUTPUT:
        - scraped_deck_id: set of ints, list of all previously scraped deck_ids
    '''

    cursor.execute('SELECT DISTINCT deck_id FROM decks')
    scraped_deck_ids = {_[0] for _ in cursor.fetchall()}

    return scraped_deck_ids

def get_event_ids(front_page, verbose=False):
    """
    Takes in a front page of mtgtop8.com and returns a list of
        the event ids

    INPUT:
        - front_page: a BeautifulSoup object of the front page

    OUTPUT:
        - event_ids: a list of all the event ids from the 'Last 10 Events' table
    """

    if verbose: print('    getting event ids from a front page')

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
        if ('&d=' in anchor['href'] and '?e=' in anchor['href']):
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

    if verbose: print('        deck request for deck id {}'.format(deck_id))

    # repeat this process a max of 5 times. If status_code==200, break
    for i in range(5):
        # preventing submitting too fast
        time.sleep(0.1 + random.random())

        try:
            response = requests.get('http://mtgtop8.com/mtgo?d={}'.format(deck_id),
                                headers={'User-Agent': 'Getting some deck lists'})

            # if good status code, quit loop and return
            # otherwise, keep going for a max of 5 times
            if response.status_code == 200:
                break

            if verbose: print('bad status code: {}. try {} of 5'.format(response.status_code, i+1))

        except:
            if verbose: print("Error connecting to http://mtgtop8.com/mtgo?d={}".format(deck_id))

    deck_list = response.text

    return deck_list

def event_request(event_id, verbose=False):
    """Takes an event_id and returns the response from the request. Errors will come later.

    INPUT:
        - event_id: the unique id for the desired event from mtgtop8.com

    OUTPUT:
        - response: the response from the get request"""

    if verbose: print('    event request for event id {}'.format(event_id))

    # repeat this process a max of 5 times. If status_code==200, break
    for i in range(5):
        # preventing submitting too fast
        time.sleep(0.1 + random.random())

        try:
            response = requests.get('http://mtgtop8.com/event?e={}'.format(event_id),
                                headers={'User-Agent': 'Getting some event info'})

            # if good status code, quit loop and return
            # otherwise, keep going for a max of 5 times
            if response.status_code == 200:
                break
            if verbose: print('bad status code: {}. try {} of 5'.format(response.status_code, i+1))
        except:
            if verbose: print("Error connecting to http://mtgtop8.com/event?e={}".format(event_id))

    return response

def modern_front_page_request(page_number=0, verbose=False):
    """Sends a get request to mtgtop8.com with the given page number

    INPUT:
        - page_number: argument for the get request. page_number of 3 gets decks from 21-30.
                       Default value of 0 to get decks from 1-10.

    OUTPUT:
        - response: the response from the get request"""

    # repeat this process a max of 5 times. If status_code==200, break
    if verbose: print('requesting front page number {}'.format(page_number))


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
            if verbose: print("Error connecting to http://mtgtop8.com/format?f=MO&meta=44&cp={}".format(page_number))

        time.sleep(0.1 + random.random())

    return response

def scrape_decklists(front_pages=[0], verbose=False):
    global conn
    global cursor
    scraped_deck_ids = get_scraped_deck_ids()
    for page_number in front_pages:
        raw_front_page = modern_front_page_request(page_number=page_number, verbose=verbose)
        front_page = BeautifulSoup(raw_front_page.text, 'html.parser')

        event_ids = get_event_ids(front_page, verbose=verbose)

        for event_id in event_ids:
            raw_event_page = event_request(event_id, verbose=verbose)
            event_page = BeautifulSoup(raw_event_page.text, 'html.parser')

            deck_ids = get_deck_ids(event_page, verbose=verbose)

            for deck_id in deck_ids:
                if int(deck_id) in scraped_deck_ids: # already scraped this deck
                    if verbose: print('        deck id {} has already been scraped'.format(deck_id))
                    continue
                raw_deck_list = deck_request(deck_id, verbose=verbose)
                deck_list = format_deck(raw_deck_list)
                if not deck_list: # empty deck list, skip this deck
                    if verbose: print('            empty deck list at deck id {}'.format(deck_id))
                    continue
                user_card_counts = make_user_card_counts(event_id, deck_id, deck_list, verbose=verbose)
                success = upload_user_card_counts(user_card_counts, verbose=verbose)

                if success:
                    conn.commit()
                else:
                    conn.rollback()
                    cursor = conn.cursor()


if __name__ == '__main__':
    scrape_decklists(verbose=True, front_pages=range(5))
