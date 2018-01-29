from flask import Flask, render_template, request
app = Flask(__name__, static_url_path='')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/input_card', methods = ['POST'])
def submit_decklist():
    # get the deck_list
    request.form.get('deck_list')

    # # get the user choices
    # white_cards = request.form.get('white_cards')
    # blue_cards = request.form.get('blue_cards')
    # black_cards = request.form.get('black_cards')
    # red_cards = request.form.get('red_cards')
    # green_cards = request.form.get('green_cards')
    # land_cards = request.form.get('land_cards')

    print(type(white_cards))
    print(white_cards)


    return jsonify()

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
