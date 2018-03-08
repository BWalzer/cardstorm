# cardstorm
### a magic: the gathering card recommender
***

Magic: the Gathering was the first trading card game, and since it's creation in 1993, Magic has grown to over 20 million players worldwide. The goal of Magic is to defeat your opponent using a deck composed of monster, spell and resource cards. While the goal is simple, choosing which cards to put into your deck is not. In the last 15 years, there have been about 80 sets of roughly 200 cards printed. As a result, players have a pool of 11,348 cards to choose from when building their deck of 60 cards.

While Magic started as a quick game to play alongside other games, a competitive scene was quickly established. Because new cards are released frequently, players must change their decks to adapt to the new cards and decks that their opponents will play. As a consequence of the fast changing meta-game, it's easy to get left behind in your deck building choices.

[cardstorm](http://www.cardstorm.me) is a web app for Magic: the Gathering players looking for cards to include in their deck. The user inputs list of cards or an incomplete deck list, and recommendations are made for cards to add to their deck. These recommendations are made based on top placing deck lists from tournaments around the world.

## How it works
Each of these steps are performed independently, on an Amazon EC2 instance and interface only with an Amazon RDS PostgreSQL database.

![Work Flow](https://github.com/BWalzer/cardstorm/blob/master/images/work_flow.png "Work Flow")

1. Using [scryfall](https://scryfall.com)'s API, a table of all Modern-legal cards is created in the PostgreSQL database. A new unique identifier is created, as there are various problems with previous unique identifiers. 

	The table of cards is updated daily, before new deck lists are scraped.

2. Deck lists (training data) are scraped from [mtgtop8](http://mtgtop8.com)'s Modern section. Each deck list is broken up into `(deck_id, card_id, card_count)` tuples in preparation of the modeling process, and inserted in to the PostgreSQL database. `card_count` is the number of copies of a unique card including in a deck (max four with a few exceptions), and it is used as a user's implicit rating of the card.
	New deck lists are scraped daily.

3. Matrix factorization is done using Spark's ALS implicit model. Implicit ratings are chosen over explicit ratings because of the following:
	* A deck including 4 copies of card A and 2 copies of card B does not mean card A is better than card B.
	* A deck not including a card in a deck does not mean the card was not wanted in the deck, the price of the card and the availability of the card are two examples of factors contributing to the number of copies included.

	The matrix factorization splits the original matrix `D` into two matrices `U, V`, where `D ~ U•V`. 
	![Step 1](https://github.com/BWalzer/cardstorm/blob/master/images/matrix_step1.png "Step 1")
	
	Normal matrix factorization models would then use `U` and `V` to get estimated ratings for un-rated items in `D`. Because one of the goals of cardstorm is to make recommendations quickly, the `V` matrix is stored in the PostgreSQL database for later use.
	![Step 2](https://github.com/BWalzer/cardstorm/blob/master/images/matrix_step2.png "Step 2")
    
   The modeling process is performed daily, after new deck lists are scraped.
   
4. Flask is used to host the web app. When a user submits a list of cards to the web app, 
![User Submission](https://github.com/BWalzer/cardstorm/blob/master/images/sample_cards.png "User Submission")
the vector `d`, a least-squares solver is used to find `u`, the solution to the system `d = u•V`.
![Step 3](https://github.com/BWalzer/cardstorm/blob/master/images/matrix_step3.png "Step 3")
Recommendations by multiplying `u•V = d'` and taking the difference between `d` and `d'`. 
![Step 4](https://github.com/BWalzer/cardstorm/blob/master/images/matrix_step4.png "Step 4")
The images corresponding to the top 10 recommendations are loaded from an s3 bucket.
![Ouput](https://github.com/BWalzer/cardstorm/blob/master/images/ouput.png "Output")








