# runs daily in crontab. gets new cards from scryfall, and new decks from mtgtop8.com
# and creates a new model

# get new cards from scryfall
/home/ubuntu/anaconda3/bin/python /home/ubuntu/cardstorm/src/card_scraping.py 1>>/home/ubuntu/cardstorm/logs/card_stdout.log 2>>/home/ubuntu/cardstorm/logs/card_stderr.log

# get new decks from mtgtop8.com
/home/ubuntu/anaconda3/bin/python /home/ubuntu/cardstorm/src/deck_scraping.py 1>>/home/ubuntu/cardstorm/logs/deck_stdout.log 2>>/home/ubuntu/cardstorm/logs/deck_stderr.log

# creates a new model
/home/ubuntu/anaconda3/bin/python /home/ubuntu/cardstorm/src/modeling.py 1>>/home/ubuntu/cardstorm/logs/model_stdout.log 2>>/home/ubuntu/cardstorm/logs/model_stderr.log
