import boto3
import os
import requests
import psycopg2
import time
from OpenSSL.SSL import SysCallError


def scrape_images():
    '''
    Scrapes images for all cards in the cards db. saves to s3 bucket
    '''

    hostname = os.environ['cardstorm_DB_HOST']
    dbname = os.environ['cardstorm_DB_DBNAME']
    username = os.environ['cardstorm_DB_USERNAME']

    conn = psycopg2.connect('dbname={} host={} user={}'.format(dbname, hostname, username))
    cursor = conn.cursor()

    s3 = boto3.client('s3')

    cursor.execute('SELECT scryfall_id, cardstorm_id, name FROM cards')

    all_cards = cursor.fetchall()
    length = len(all_cards)
    counter = 1
    for scryfall_id, cardstorm_id, name in all_cards:
        url = 'https://api.scryfall.com/cards/{}?format=image'.format(scryfall_id)
        try:
            image = requests.get(url)
            s3.put_object(Bucket='mtg-capstone', Key='card_images/jpg/{}.jpg'.format(cardstorm_id), Body=image.content)
        except SysCallError:
            print('\tproblem getting image for {}'.format(name))

        print('{} done, {}/{}'.format(name.lower(), counter, length))

        counter += 1

if __name__ == '__main__':
    scrape_images()
