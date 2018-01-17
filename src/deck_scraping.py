import requests
import re
import json
import random
import time
import boto3
from bs4 import BeautifulSoup

s3 = boto3.client('s3')

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
