from flask import Flask, render_template, request, jsonify
from predictions import CardRecommender

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommendations', methods = ['POST'])
def get_recommendations():
    user_submission = request.json

    raw_deck_list = user_submission["deckList"]
    filters = user_submission['filters']
    print(filters)
    print(type(filters))

    card_recommender = CardRecommender()
    card_recommender.fit(raw_deck_list)
    recommendations= card_recommender.recommend(land_filter=filters['land'],
                        white_filter=filters['white'], blue_filter=filters['blue'],
                        black_filter=filters['black'], red_filter=filters['red'],
                        green_filter=filters['green'], colorless_filter=filters['colorless'])

    card_images = [f'http://mtg-capstone.s3-website-us-west-2.amazonaws.com/card_images/jpg/{cardstorm_id}.jpg' for cardstorm_id in recommendations[:10]]

    return jsonify(card_images)


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
