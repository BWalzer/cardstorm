# runs daily in crontab. gets new cards from scryfall, and new decks from mtgtop8.com
# and creates a new model

# get new cards from scryfall
/home/ubuntu/anaconda3/bin/python3 /home/ubuntu/cardstorm/src/card_scraping.py 1>/home/ubuntu/cardstorm_logs/card_stdout.log 2>/home/ubuntu/cardstorm_logs/card_stderr.log

# get new decks from mtgtop8.com
/home/ubuntu/anaconda3/bin/python3 /home/ubuntu/cardstorm/src/deck_scraping.py 1>/home/ubuntu/cardstorm_logs/deck_stdout.log 2>/home/ubuntu/cardstorm_logs/deck_stderr.log

# creates a new model
/home/ubuntu/anaconda3/bin/python3 /home/ubuntu/cardstorm/scripts/modeling.sh
