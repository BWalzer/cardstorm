import requests
import json
import deck_scraping
import time
import random

def scrape_modern_cards(verbose=False):
    """
    Scrapes the
    INPUT:
        - verbose: If True, status updates will be printed to the console.

    OUTPUT:
        - list of lists of card dictionaries
    """

    # initial url to send a request to
    url = 'https://api.scryfall.com/cards/search?q=format:modern'

    modern_legal_cards = []
    total_pages = 0

    # continue as long as there are more cards to get
    while True:
        response = requests.get(url,
                    headers={'User-Agent': 'Getting modern legal cards'})

        # check for good status code
        if response.status_code != 200 and verbose:
            print('Bad statud code on page {}: {}'.format(total_pages,
                                                        response.status_code))

        # load the json response
        cards = json.loads(response.text)

        # 'has_more' indicates if there are more cards to get. If it is false,
        # we're done getting the cards.
        if not cards['has_more']:
            if verbose: print('All done! {} pages recieved.'.format(total_pages))
            break

        modern_legal_cards.append(cards)
        total_pages += 1
        url = cards['next_page']

        time.sleep(0.05 + random.random())

        if verbose: print('Page request #{} successful!'.format(total_pages))

    return modern_legal_cards

def make_card_dict(modern_legal_cards):
    """
    Turns the list of modern legal cards into a dictionary of cards with card names
        as keys and scryfall card ids as values.

    INPUT:
        - modern_legal_cards: list of modern legal cards, this is returned from
                              scrape_modern_cards

    OUTPUT:
        - card_dict: a dictionary of cards with card names as keys and scryfall card
                     ids as values.
    """

    for page in modern_legal_cards:
        for card in page:
            card_dict[card['name']] = card['id']

    return card_dict

if __name__ == '__main__':
    modern_legal_cards = scrape_modern_cards(verbose=True)
    card_dict = make_card_dict(modern_legal_cards)
