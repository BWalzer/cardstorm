import requests
import re
import random
import time
from bs4 import BeautifulSoup


def get_event_ids(front_page):
    """Takes in the front page of mtgtop8.com and returns a list of all the event ids

    INPUT:
        - front_page: BeautifulSoup object of the event page

    OUTPUT:
        - event_ids: List of all the event ids from the 'Last 10 Events' table"""

    event_list = [event['href'] for event in front_page.find_all('table')[2]
                  .find('td').find_next_sibling().find_all('table')[1].find_all('a')]

    # use map() and regular expressions to get the event id out of the anchor tags
    event_ids = list(map(lambda x: re.search("e=(\d+)&", x).group(1), event_list))

    return event_ids

def get_deck_ids(event_page):
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

def deck_request(deck_id):
    """Takes a deck_id and returns the response from the request. Errors will come later.

    INPUT:
        - deck_id: the unique id for the desired deck list from mtgtop8.com

    OUTPUT:
        - response: the response from the get request"""

    response = requests.get('http://mtgtop8.com/mtgo?d={}'.format(deck_id),
                            headers={'User-Agent': 'Getting some deck lists'})

    # FUTURE WORK: check the status code
    return response

def deck_requests(deck_ids):
    """Takes a list of deck ids and returns the responses from the requests. Errors will come later.

    INPUT:
        - deck_ids: the unique ids for each ofthe desired deck lists from mtgtop8.com

    OUTPUT:
        - responses: the responses from the get requests"""

    responses = []
    for deck_id in deck_ids:
        response = deck_request(deck_id)
        responses.append(response)

    # FUTURE WORK: check the status code
    return responses

def event_request(event_id):
    """Takes an event_id and returns the response from the request. Errors will come later.

    INPUT:
        - event_id: the unique id for the desired event from mtgtop8.com

    OUTPUT:
        - response: the response from the get request"""

    response = requests.get('http://mtgtop8.com/event?e={}'.format(event_id),
                            headers={'User-Agent': 'Getting some event info'})

    # FUTURE WORK: check the status code
    return response

def event_requests(event_ids):
    """Takes a list of event ids and returns a list of responses from the requests. Errors will come later.

    INPUT:
        - event_ids: the list of unique ids for the desired events from mtgtop8.com

    OUTPUT:
        - responses: the list of responses from the get requests"""

    responses = []
    for event_ids in event_ids:
        response = event_request(event_id)
        responses.append(response)

    # FUTURE WORK: check the status code
    return responses

def modern_front_page_request(page_number=0):
    """Sends a get request to mtgtop8.com with the given page number

    INPUT:
        - page_number: argument for the get request. page_number of 3 gets decks from 21-30.
                       Default value of 0 to get decks from 1-10.

    OUTPUT:
        - response: the response from the get request"""

    response = requests.get('http://mtgtop8.com/format?f=MO&meta=44&cp={}'.format(page_number),
                            headers={'User-Agent': 'Modern front page request'})

    # FUTURE WORK: check the status code
    return response
