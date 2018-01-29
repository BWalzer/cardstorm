from flask import Flask, render_template, request, jsonify
from predictions import make_recommendations
app = Flask(__name__, static_url_path='')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommendations', methods = ['POST'])
def submit_decklist():
    # get the deck_list
    raw_deck_list = request.form.get('deck_list')

    print(raw_deck_list)
    # # get the user choices
    # white_cards = request.form.get('white_cards')
    # blue_cards = request.form.get('blue_cards')
    # black_cards = request.form.get('black_cards')
    # red_cards = request.form.get('red_cards')
    # green_cards = request.form.get('green_cards')
    # land_cards = request.form.get('land_cards')

    top_10 = make_recommendations(raw_deck_list, 10)
    card_images = ['https://s3-us-west-2.amazonaws.com/mtg-capstone/card_images/{}.jpg'.format(cardstorm_id) for cardstorm_id in top_10]

    print(card_images)

    # return jsonify(image_1: )

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
