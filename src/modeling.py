import pyspark as ps
import psycopg2
import os
import datetime
import multiprocessing
# from pyspark.mllib.recommendation import ALS
from pyspark.sql.types import StructField, StructType, IntegerType
from pyspark.ml.recommendation import ALS

def get_deck_card_counts(schema):
    '''
    Gets the deck data needed for the Spark ALS model.

    INPUT:
        - schema: StructType object, schema for spark ratings df

    OUTPUT:
        - incomplete_ratings: Spark df, ratings for all deck-card combos found in real decks
    '''

    cursor.execute('SELECT deck_id, cardstorm_id, card_count FROM decks')

    incomplete_ratings = spark.createDataFrame(data=cursor.fetchall(),
                                               schema=schema)
    incomplete_ratings_rdd = incomplete_ratings.rdd.repartition(1000)
    incomplete_ratings = spark.createDataFrame(incomplete_ratings_rdd,
                                               schema=schema)
    return incomplete_ratings

def get_unused_cardstorm_ids():
    '''
    Gets a list of all the unused cardstorm_ids from the db

    INPUT:
        NONE

    OUTPUT:
        - unused_ids: list of ints, all unused cardstorm_ids.
    '''

    cursor.execute('''SELECT cardstorm_id
                      FROM cards
                      WHERE cardstorm_id
                        NOT IN (SELECT DISTINCT cardstorm_id FROM decks)''')

    unused_ids = [_[0] for _ in cursor.fetchall()]

    return unused_ids

def fill_unused_cardstorm_ids(unused_ids):
    '''
    Creates fake date for all unused cardstorm_ids.

    INPUT:
        - unused_ids: list of ints, all cardstorm_ids that don't show up in a deck

    OUTPUT:
        - filler_data: list of tuples, deck_id - cardstorm_id - card_count for
                        each of the unused_ids. deck_id is '-1' to easily id them
    '''

    filler_data = []
    for unused_id in unused_ids:
        filler_data.append((-1, unused_id, 1))

    return filler_data

def upload_product_rdd(product_rdd):
    '''
    Adds the product features rdd from the spark ALS model to the db.

    INPUT:
        - product_rdd: Spark rdd, features pulled from fitted Spark ALS model

    OUTPUT:
        - success: bool, True if no problems were encountered.
    '''
    current_date = str(datetime.date.today())

    cursor.execute('SELECT MAX(run_id) FROM product_matrices')
    run_id = cursor.fetchone()[0]
    if run_id is None:
        run_id = 0
    run_id += 1

    for cardstorm_id, features in product_rdd.collect():
        query = '''INSERT INTO product_matrices (cardstorm_id, features, date, run_id)
                   VALUES (%s, %s, %s, %s)'''

        try:
            cursor.execute(query, vars=[cardstorm_id, features, current_date, run_id])
        except psycopg2.IntegrityError:
            return False
            continue

    return True

def make_recommender():
    '''
    Makes the recommender model! Gets deck data from the database, makes filler
    data for unused cards, uses Spark ALS to train a model of implicit ratings.
    Pulls out the product features matrix (often referred to as V) and
    uploads it to the database with the current data attached.

    INPUT:
        NONE

    OUTPUT:
        NONE

    Does everything

        Get deck data from db
        create schema for spark DF
        get unused cardstorm_ids
        create fake data for all unused cards
        make new spark df from unused cards
        merge dataframes
        create and train ALS implicit model
        get the product matrix
        upload df to db
    '''

    ratings_schema = StructType([StructField('deck_id', IntegerType()),
                                 StructField('cardstorm_id', IntegerType()),
                                 StructField('card_count', IntegerType())])

    incomplete_ratings = get_deck_card_counts(schema=ratings_schema)

    unused_ids = get_unused_cardstorm_ids()

    filler_data = fill_unused_cardstorm_ids(unused_ids)

    filler_ratings = spark.createDataFrame(data=filler_data,
                                           schema=ratings_schema)
    ratings_df = incomplete_ratings.union(filler_ratings)

    # model = ALS.trainImplicit(ratings=ratings_df, rank=30)
    model = ALS(rank=30, implicitPrefs=True, userCol='deck_id', maxIter=20,
                itemCol='cardstorm_id', ratingCol='card_count')
    fitted_model = model.fit(ratings_df)

    product_df = fitted_model.itemFactors

    upload_status = upload_product_rdd(product_df)

    if upload_status: conn.commit()

def main():
    print('#####################################################')
    print('BEGIN MODELING: {}'.format(datetime.datetime.today()))
    global dbname, host, username, password, conn, cursor, spark
    dbname = os.environ['CARDSTORM_DB_DBNAME']
    host = os.environ['CARDSTORM_DB_HOST']
    username = os.environ['CARDSTORM_DB_USERNAME']
    password = os.environ['CARDSTORM_DB_PASSWORD']


    conn = psycopg2.connect('dbname={} host={} user={} password={}'.format(dbname, host, username, password))
    cursor = conn.cursor()

    spark = (ps.sql.SparkSession.builder
                   .master('local[{}]'.format(multiprocessing.cpu_count()))
                   .appName('cardstorm modeling')
                   .getOrCreate())

    spark.sparkContext.setLogLevel('WARN')
    make_recommender()

    conn.close()

if __name__ == '__main__':
    main()
