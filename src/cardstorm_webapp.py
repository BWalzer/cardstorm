from flask import Flask, render_template, request, jsonify
from predictions import make_recommendations
app = Flask(__name__, static_url_path='')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommendations', methods = ['POST'])
def submit_decklist():
    # get the deck_list
    user_submission = request.get_data()
    print(user_submission)
    # raw_deck_list = user_submission['deckList']
    # print(raw_deck_list)

    # # get the user choices
    # white_cards = request.form.get('white_cards')
    # blue_cards = request.form.get('blue_cards')
    # black_cards = request.form.get('black_cards')
    # red_cards = request.form.get('red_cards')
    # green_cards = request.form.get('green_cards')
    # land_cards = request.form.get('land_cards')

    top_10 = make_recommendations(user_submission.decode(), 10)
    card_images = [f'http://mtg-capstone.s3-website-us-west-2.amazonaws.com/card_images/jpg/{cardstorm_id}.jpg' for cardstorm_id in top_10]

    return jsonify(card_images)



if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
