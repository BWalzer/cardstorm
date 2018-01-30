import psycopg2
import os
from deck_scraping import format_deck, ReflexiveDict, parse_card_string
import numpy as np

dbname = os.environ['CAPSTONE_DB_DBNAME']
host = os.environ['CAPSTONE_DB_HOST']
username = os.environ['CAPSTONE_DB_USERNAME']
password = os.environ['CAPSTONE_DB_PASSWORD']

conn = psycopg2.connect('dbname={} host={} user={} password={}'.format(dbname, host, username, password))
cursor = conn.cursor()

def deck_to_dict(deck_list, card_dict):
    '''
        Turns a raw deck_list into a dictionary with cardstorm ids as keys
        and counts as values

        INPUT:
            - deck_list: string, plaintext deck list with \n between each card line
            - card_dict: ReflexiveDict object, dictionary with all cards and
                            cardstorm_ids pointing to each other

        OUTPUT:
            - deck_dict: dictionary, dict with cardstorm ids as keys and lowercase
                            card counts as values
    '''
    deck_dict = {}
    for card_string in deck_list.split('\n'):
        if card_string.startswith('S'):
            break
        if not card_string:
            break
        parse_status, card_name, card_count = parse_card_string(card_string)
        try:
            cardstorm_id = card_dict[card_name.lower()]
        except KeyError:
            print('card "{}" not found'.format(card_name))
        deck_dict[cardstorm_id] = int(card_count)

    return deck_dict

def vectorize_deck(all_cardstorm_ids, deck_dict):
    '''
        Creates an (n x 1) vector, where n is the number of available cards

        INPUT:
            - all_cardstorm_ids: numpy array of all the available cardstorm_ids
            - deck_dict: dict representation of user submitted deck list. keys
                            are cardstorm_ids and values are card counts
        OUTPUT:
            - deck_vector: numpy array of shape (n x 1), where n is the number of
                            cardstorm_ids in all_cardstorm_ids. Each entry corresponds
                            to the corresponding cardstorm_id in all_cardstorm_ids,
                            and it is either the count of the card in the deck or 0
                            if it's not included in the deck.
    '''

    deck_vector = []

    for cardstorm_id in all_cardstorm_ids:
        if cardstorm_id in deck_dict:
            deck_vector.append(deck_dict[cardstorm_id])
        else:
            deck_vector.append(0)

    deck_vector = np.array(deck_vector)

    return deck_vector

def get_feature_matrix():
    '''
        Pulls the most recent feature matrix from the databse and formats it properly

        INPUT:
            NONE
        OUTPUT:
            - feature_matrix: numpy array of size (n x k), where n is the number of
                                cards and k is chosen in the modeling process
    '''
    global cursor
    query = '''SELECT cardstorm_id, features
               FROM product_matrices
               WHERE date = (SELECT MAX(date) FROM product_matrices)
               ORDER BY cardstorm_id ASC'''
    cursor.execute(query)

    feature_matrix = []

    for cardstorm_id, features in cursor.fetchall():
        feature_matrix.append(features)

    feature_matrix = np.array(feature_matrix)

    return feature_matrix

def solve_system(feature_matrix, deck_vector):
    '''
        Gets the least squares solution to the problem.

        INPUT:
            - feature_matrix: numpy array of shape (n x k), where n is the number of
                                cards and k is chosen in the modeling process
            - deck_vector: numpy array of shape (n x 1), where n is the number of
                            cards

        OUTPUT:
            - u_vector: numpy array, the least squares solution to the system
                            deck_vector = (u_vector)*(feature_matrix)
    '''

    if len(deck_vector) > 0:
        u_vector = np.linalg.lstsq(feature_matrix, deck_vector)[0]
    else:
        return np.array([])

    return u_vector

def top_n_recommendations(recommendations, deck_vector, all_cardstorm_ids, n=10):
    '''
        Gets the top n recommendations from the recreated deck list

        INPUT:
            - recommendations: numpy array, the recreated deck_vector with predictions filled in
            - deck_vector: numpy array, the original deck_vector
            - n: int, the number of recommendations desired. default 10

        OUTPUT:
            top_recommendations: numpy array, the top n recommendations in descending order
    '''
    top_recommendations = all_cardstorm_ids[np.argsort(recommendations - deck_vector)[:-n-1:-1]]

    return top_recommendations

def make_recommendations(raw_deck_list, num_top_recommendations=10):
    '''

        get all cardstorm ids
        read user submitted deck file
        make deck dictionary
        make deck vector
        get feature matrix from db
        solve for u
        get recommendations

    '''
    card_dict = ReflexiveDict()
    all_cardstorm_ids = card_dict.get_cardstorm_ids()

    deck_dict = deck_to_dict(raw_deck_list, card_dict)

    deck_vector = vectorize_deck(all_cardstorm_ids, deck_dict)

    feature_matrix = get_feature_matrix()

    u_vector = solve_system(feature_matrix, deck_vector)

    if len(u_vector) == 0: # something went wrong
        print('deck vector was empty')
        return

    recommendations = np.dot(u_vector, feature_matrix.T)

    top_recommendations = top_n_recommendations(recommendations, deck_vector, all_cardstorm_ids, n=num_top_recommendations)

    return top_recommendations
