import requests
import re
import random
import time
import pickle
from bs4 import BeautifulSoup

def get_event_ids(front_page):
    """
    Takes in a front page of mtgtop8.com and returns a list of
        the event ids

    INPUT:
        - front_page: a BeautifulSoup object of the front page

    OUTPUT:
        - event_ids: a list of all the event ids from the 'Last 10 Events' table
    """

    print('\tGetting event ids from a front page')

    event_list = [event['href'] for event in front_page.find_all('table')[2]
         .find('td').find_next_sibling().find_all('table')[1].find_all('a')]

    # use map() and regular expressions to get the event id out of the anchor tags
    event_ids = list(map(lambda x: re.search("e=(\d+)&", x).group(1),
                                                        event_list))

    return event_ids

def get_all_event_ids(front_pages):
    """
    Takes in a list of front pages of mtgtop8.com and returns a list of all
        the event ids

    INPUT:
        - front_pages: a list of BeautifulSoup object of the event page

    OUTPUT:
        - all_event_ids: a set of all the event ids from the 'Last 10 Events' table
    """

    all_event_ids = set()
    for front_page in front_pages:
        event_ids = get_event_ids(front_page)
        all_event_ids.update(event_ids)

    return all_event_ids

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
        - deck_list: a list of strings representing the deck list corresponding
                     to the deck_id."""

    print('\t\tDeck request for deck id {}'.format(deck_id))
    response = requests.get('http://mtgtop8.com/mtgo?d={}'.format(deck_id),
                            headers={'User-Agent': 'Getting some deck lists'})

    deck_list = response.text.split('\r\n')

    # preventing submitting too fast
    time.sleep(2 + random.random())

    # FUTURE WORK: check the status code
    return deck_list

def deck_requests(deck_ids):
    """Takes a set of deck ids and returns the responses from the requests. Errors will come later.

    INPUT:
        - deck_ids: the set of unique ids for each ofthe desired deck lists from mtgtop8.com

    OUTPUT:
        - deck_lists: a dictionary with key=deck_id and value=deck_list"""

    deck_lists = {}
    for deck_id in deck_ids:
        deck_list = deck_request(deck_id)
        deck_lists[deck_id] = deck_list

    # FUTURE WORK: check the status code
    return deck_lists

def event_request(event_id):
    """Takes an event_id and returns the response from the request. Errors will come later.

    INPUT:
        - event_id: the unique id for the desired event from mtgtop8.com

    OUTPUT:
        - response: the response from the get request"""

    print('\t\tEvent request for event id {}'.format(event_id))
    response = requests.get('http://mtgtop8.com/event?e={}'.format(event_id),
                            headers={'User-Agent': 'Getting some event info'})

    # preventing submitting too fast
    time.sleep(2 + random.random())

    # FUTURE WORK: check the status code
    return response

def event_requests(event_ids):
    """
    Takes a list of event ids and returns a list of BeautifulSoup objects of
    the responses from the requests. Errors will come later.

    INPUT:
        - event_ids: the list of unique ids for the desired events from
                     mtgtop8.com

    OUTPUT:
        - event_pages: the list of BeautifulSoup objects of the responses from
                       the get requests
    """

    event_pages = []
    for event_id in event_ids:
        event_page = BeautifulSoup(event_request(event_id).text, 'html.parser')
        event_pages.append(event_page)

    # FUTURE WORK: check the status code
    return event_pages

def modern_front_page_request(page_number=0):
    """Sends a get request to mtgtop8.com with the given page number

    INPUT:
        - page_number: argument for the get request. page_number of 3 gets decks from 21-30.
                       Default value of 0 to get decks from 1-10.

    OUTPUT:
        - response: the response from the get request"""

    print('\tRequesting front page number {}'.format(page_number))

    response = requests.get('http://mtgtop8.com/format?f=MO&meta=44&cp={}'.format(page_number),
                            headers={'User-Agent': 'Modern front page request'})


    time.sleep(2 + random.random())

    # FUTURE WORK: check the status code
    return response

def modern_front_page_requests(page_numbers=[0]):
    """
    Sends a get request to get the modern front page from mtgtop8.com. One
        request is made for each value in page_numbers.

    INPUT:
        - page_numbers: a list of values for 'cp' in the get request to mtgtop8.
                        Default value of [0].

    OUTPUT:
        - front_pages: a list of BeautifulSoup objects for each of the modern
                       front pages.
    """

    front_pages = []
    for page_number in page_numbers:
        response = modern_front_page_request(page_number)
        front_page = BeautifulSoup(response.text, 'html.parser')
        front_pages.append(front_page)

    # FUTURE WORK: check the status code
    return front_pages

def get_deck_lists(event_ids):
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
        event_page = BeautifulSoup(event_request(event_id).text, 'html.parser')

        # update the set of deck ids with result from get_deck_ids()
        deck_ids.update(get_deck_ids(event_page))

    # get a deck list for each deck id, in a dictionary with key=deck_id and
    # value=deck list
    deck_lists = deck_requests(deck_ids)

    return deck_lists

def scrape_deck_lists():
    """
    Does the entire web scraping process. Requests the front page of

    INPUT: NONE

    OUTPUT:
        - deck_lists: a dictionary of deck lists with key=deck_id and
                      value=deck_list
    """

    # get the modern page with the first 10 events
    print('Requesting the front pages')
    front_pages = modern_front_page_requests(range(10)) # leaving page_numbers blank for now

    # get the event ids from the page with the first 10 events
    print('Getting all event ids')
    event_ids = get_all_event_ids(front_pages)

    # using event ids, get a set of deck lists
    print('Getting deck lists')
    deck_lists = get_deck_lists(event_ids)

    return deck_lists

if __name__ == '__main__':
    start_time = time.time()
    deck_lists = scrape_deck_lists()
    end_time = time.time()

    print('{} decks scraped! Duration: {}'.format(len(deck_lists),
                                            end_time - start_time))


    pickle.dump(deck_lists, open('deck_lists', 'bw'))
    print('Deck lists pickled!')
