import requests
import json
import psycopg2
import os


def format_card(card):
    '''
    Formats cards in a db friendly manner. If the card is multifaced, the first face is used for missing fields

    INPUT:
        - card: dictionary, magic card from scryfall.com

    OUTPUT:
        - formatted_card: list, attributes of each card in the following order:
                            [name, cmc, type_line, oracle_text, mana_cost, power, toughness, colors,
                            color_identity, legalities, set_code, set_name, collector_number, scryfall_id]
    '''
    keys = card.keys()
    formatted_card = []
    if 'card_faces' in keys:
        # multifaced card
        front_face = card['card_faces'][0]
        front_keys = front_face.keys()

        formatted_card.append(card['name'])
        formatted_card.append(card['cmc'])
        formatted_card.append(front_face['type_line'])

        if 'oracle_text' in front_keys:
            formatted_card.append(front_face['oracle_text'])
        else:
            formatted_card.append(None)

        formatted_card.append(front_face['mana_cost'])

        if 'power' in front_keys:
            formatted_card.append(front_face['power'])
        else:
            formatted_card.append(None)

        if 'toughness' in front_keys:
            formatted_card.append(front_face['toughness'])
        else:
            formatted_card.append(None)

        if 'colors' in keys:
            formatted_card.append(card['colors'])
        else:
            formatted_card.append(front_face['colors'])

        formatted_card.append(card['color_identity'])

        legalities = [k for k, v in card['legalities'].items() if v == 'legal']
        formatted_card.append(legalities)

        formatted_card.append(card['set'])
        formatted_card.append(card['set_name'])
        formatted_card.append(card['collector_number'])
        formatted_card.append(card['id'])

    else:
        # single faced card
        formatted_card.append(card['name'])
        formatted_card.append(card['cmc'])
        formatted_card.append(card['type_line'])

        if 'oracle_text' in keys:
            formatted_card.append(card['oracle_text'])
        else:
            formatted_card.append(None)

        formatted_card.append(card['mana_cost'])

        if 'power' in keys:
            formatted_card.append(card['power'])
        else:
            formatted_card.append(None)

        if 'toughness' in keys:
            formatted_card.append(card['toughness'])
        else:
            formatted_card.append(None)

        formatted_card.append(card['colors'])
        formatted_card.append(card['color_identity'])

        legalities = [k for k, v in card['legalities'].items() if v == 'legal']
        formatted_card.append(legalities)
        formatted_card.append(card['set'])
        formatted_card.append(card['set_name'])
        formatted_card.append(card['collector_number'])
        formatted_card.append(card['id'])

    return formatted_card

def upload_card(card, cursor, verbose=False):

    template = ', '.join(['%s'] * len(card))

    query = '''INSERT INTO cards (name, cmc, type_line, oracle_text, mana_cost, power, toughness, colors,
                              color_identity, legalities, set_id, set_name, collector_number, scryfall_id)
           VALUES ({})'''.format(template)

    try:
        cursor.execute(query, card)
        return True

    except psycopg2.IntegrityError:
        if verbose: print('duplicate card detected')
        return False

def scrape_modern_cards(verbose=False):
    hostname = os.environ['CAPSTONE_DB_HOST']
    dbname = os.environ['CAPSTONE_DB_DBNAME']
    username = os.environ['CAPSTONE_DB_USERNAME']
    password = os.environ['CAPSTONE_DB_PASSWORD']

    conn = psycopg2.connect('dbname={} host={} user={} password={}'.format(dbname, hostname, username, password))
    cursor = conn.cursor()

    url = 'https://api.scryfall.com/cards/search?q=format:modern'

    while True:
        if verbose: print('requsting scryfall api')
        response = requests.get(url)
        json_response = json.loads(response.text)

        if verbose: print('processing cards')
        for i, raw_card in enumerate(json_response['data']):
            if verbose: print('{}'.format(i), end=', ')
            card = format_card(raw_card)
            if verbose: print('{}'.format(card[0]), end=', ')
            status = upload_card(card, cursor, verbose=verbose)

            if status:
                conn.commit()
            else:
                conn = psycopg2.connect('dbname={} host={} user={} password={}'.format(dbname, hostname, username, password))
                cursor = conn.cursor()

        if not json_response['has_more']:
            if verbose: print('all done!')
            break

        if verbose: print('getting new url')
        url = json_response['next_page']

if __name__ == '__main__':
    scrape_modern_cards(True)
