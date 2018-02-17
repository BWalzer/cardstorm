import requests
import json
import psycopg2
import os
import datetime

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
    formatted_card = []
    layout = card['layout']
    keys = card.keys()
    if layout == 'normal' or layout == 'leveler':
        # normal layout, i.e, Lightning Bolt
        formatted_card.append(card['name'].lower())
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
        formatted_card.append(card['layout'])

    elif layout == 'split':
        # split layout, i.e, (Dusk // Dawn), (Boom // Bust)
        side_a = card['card_faces'][0]
        side_b = card['card_faces'][1]

        formatted_card.append(card['name'].lower())
        formatted_card.append(card['cmc'])
        formatted_card.append(' // '.join([side_a['type_line'], side_b['type_line']]))
        formatted_card.append(' // '.join([side_a['oracle_text'], side_b['oracle_text']]))
        formatted_card.append(card['mana_cost'])
        formatted_card.append(None)
        formatted_card.append(None)
        formatted_card.append(card['colors'])
        formatted_card.append(card['color_identity'])
        legalities = [k for k, v in card['legalities'].items() if v == 'legal']
        formatted_card.append(legalities)
        formatted_card.append(card['set'])
        formatted_card.append(card['set_name'])
        formatted_card.append(card['collector_number'])
        formatted_card.append(card['id'])
        formatted_card.append(card['layout'])

    elif layout == 'flip':
        # flip layout, i.e, Akki Lavarunner
        side_a = card['card_faces'][0]
        side_b = card['card_faces'][1]

        formatted_card.append(side_a['name'].lower())
        formatted_card.append(card['cmc'])
        formatted_card.append(' // '.join([side_a['type_line'], side_b['type_line']]))
        formatted_card.append(' // '.join([side_a['oracle_text'], side_b['oracle_text']]))
        formatted_card.append(card['mana_cost'])
        formatted_card.append(side_a['power'])
        formatted_card.append(side_a['toughness'])
        formatted_card.append(card['colors'])
        formatted_card.append(card['color_identity'])
        legalities = [k for k, v in card['legalities'].items() if v == 'legal']
        formatted_card.append(legalities)
        formatted_card.append(card['set'])
        formatted_card.append(card['set_name'])
        formatted_card.append(card['collector_number'])
        formatted_card.append(card['id'])
        formatted_card.append(card['layout'])

    elif layout == 'transform':
        # transform layout, i.e, Delver of Secrets
        side_a = card['card_faces'][0]
        side_b = card['card_faces'][1]

        side_a_keys = side_a.keys()
        side_b_keys = side_b.keys()

        formatted_card.append(side_a['name'].lower())
        formatted_card.append(card['cmc'])
        formatted_card.append(' // '.join([side_a['type_line'], side_b['type_line']]))
        if 'oracle_text' in side_a_keys: a_oracle_text = side_a['oracle_text']
        else: a_oracle_text = ''
        if 'oracle_text' in side_b_keys: b_oracle_text = side_b['oracle_text']
        else: b_oracle_text = ''
        formatted_card.append(' // '.join([a_oracle_text, b_oracle_text]))
        formatted_card.append(side_a['mana_cost'])
        if 'power' in side_a_keys:
            formatted_card.append(side_a['power'])
        else:
            formatted_card.append(None)
        if 'toughness' in side_a_keys:
            formatted_card.append(side_a['toughness'])
        else:
            formatted_card.append(None)
        formatted_card.append(side_a['colors'] + side_b['colors'])
        formatted_card.append(card['color_identity'])
        legalities = [k for k, v in card['legalities'].items() if v == 'legal']
        formatted_card.append(legalities)
        formatted_card.append(card['set'])
        formatted_card.append(card['set_name'])
        formatted_card.append(card['collector_number'])
        formatted_card.append(card['id'])
        formatted_card.append(card['layout'])

    elif layout == 'meld':
        # meld layout, i.e, Bruna, the Fading Light
        # this layout turns out to be pretty much the same as a normal card
        formatted_card.append(card['name'].lower())
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
        formatted_card.append(card['layout'])

    return formatted_card

def upload_card(card, cursor, verbose=False):

    template = ', '.join(['%s'] * len(card))

    query = '''INSERT INTO cards (name, cmc, type_line, oracle_text, mana_cost, power, toughness, colors,
                              color_identity, legalities, set_id, set_name, collector_number, scryfall_id, layout)
           VALUES ({})'''.format(template)

    try:
        cursor.execute(query, card)
        return True

    except psycopg2.IntegrityError:
        if verbose: print('duplicate card detected')
        return False

def scrape_modern_cards(verbose=False):
    if verbose: print('SCRAPING CARDS: {}'.format(datetime.datetime.today()))
    hostname = os.environ['CARDSTORM_DB_HOST']
    dbname = os.environ['CARDSTORM_DB_DBNAME']
    username = os.environ['CARDSTORM_DB_USERNAME']
    password = os.environ['CARDSTORM_DB_PASSWORD']

    conn = psycopg2.connect('dbname={} host={} user={} password={}'.format(dbname, hostname, username, password))
    cursor = conn.cursor()

    url = 'https://api.scryfall.com/cards/search?q=format:modern'

    while True:
        if verbose: print('requsting scryfall api')
        response = requests.get(url)
        json_response = json.loads(response.text)

        if verbose: print('processing cards')
        for i, raw_card in enumerate(json_response['data']):
            if verbose: print('{}, "{}"'.format(i, raw_card['name']))
            card = format_card(raw_card)
            status = upload_card(card, cursor, verbose=verbose)

            if status:
                conn.commit()
            else:
                conn.rollback()
                cursor = conn.cursor()
        if not json_response['has_more']:
            if verbose: print('all done!')
            break

        if verbose: print('getting new url')
        url = json_response['next_page']

if __name__ == '__main__':
    scrape_modern_cards(True)
