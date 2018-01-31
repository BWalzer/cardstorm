from flask import Flask, render_template, request, jsonify
from predictions import CardRecommender

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommendations', methods = ['POST'])
def get_recommendations():
    raw_deck_list = request.get_data().decode()

    card_recommender = CardRecommender()
    card_recommender.fit(raw_deck_list)
    recommendations= card_recommender.recommend()

    card_images = [f'http://mtg-capstone.s3-website-us-west-2.amazonaws.com/card_images/jpg/{cardstorm_id}.jpg' for cardstorm_id in recommendations[:10]]

    return jsonify(card_images)


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
