import pickle, sys
from sentiment_analyses.azure_sentiment import azure_sentiment_score
# from sentiment_analyses.google_sentiment import GCP as google_sentiment_score
from sentiment_analyses.amazon_sentiment import AWS_SWAG as amazon_sentiment_score
from random import shuffle, randint
from CAH_Keanu import initialise_prior, Update_After_Win, freq_expectation, from_posterior
import numpy as np
import pymc3 as pm
from pymc3 import Normal

class GameState:
    """Store the gamestate."""

    def __init__(self, n_human_players=1, n_ai_players=1, n_cards=10):
        """Initialise the gamestate and players."""

        self.n_cards = n_cards

        # Load the answers
        with open("cards-against-humanity/answers.pickle", 'rb') as ans:
            self.answer_cards = pickle.load(ans)
            shuffle(self.answer_cards)
        self.used_answers = 0

        # Load the questions
        with open("cards-against-humanity/questions.pickle", 'rb') as qs:
            self.question_cards = pickle.load(qs)
            shuffle(self.question_cards)
        self.used_questions = 0

        # Make the human players
        self.human_players = []
        for _ in range(n_human_players):
            self.human_players.append(HumanPlayer(Player(self, n_cards)))

        # Make the AI players
        self.ai_players = []
        for _ in range(n_ai_players):
            self.ai_players.append(AIPlayer(Player(self, n_cards)))

    def pop_ans(self, n_cards):
        """Pop the top n cards"""

        cards = self.answer_cards[self.used_answers : self.used_answers + n_cards]
        self.used_answers += n_cards

        return cards

    def pop_q(self):
        """Pop the next question card"""

        card = self.question_cards[self.used_questions]
        self.used_questions += 1

        while card.count("_") != 1:
            card = self.question_cards[self.used_questions]
            self.used_questions += 1

        self.current_question = card

        return self.current_question

    def set_question(self, q):
        self.current_question = q

    def choose_ai_answer(self):
        score_list=[]
        for i in self.ai_players[0].player.card_strings:
            phrase = self.current_question.replace("_", i)

            temp = amazon_sentiment_score(phrase)
            temp_sum = temp['Positive']+temp['Negative']
            current_score=(temp['Positive']-temp['Negative'])/temp_sum
            score_list.append((current_score+1)/2)

        results = freq_expectation(np.array(score_list), self.ai_players[0].trace)
        print(results)
        my_answer= self.ai_players[0].player.card_strings[np.argmax(results)]
        return self.current_question.replace("_", my_answer )

class Player:
    """Contains common functions"""
    def __init__(self, game, n_cards):
        self.card_strings = game.pop_ans(n_cards)

    def display_cards(self):
        for i in range(len(self.card_strings)):
            print(str(i+1) + ".", self.card_strings[i])

class HumanPlayer(Player):
    """Human player state"""
    def __init__(self, parent):
        self.player = parent

class AIPlayer(Player):
    def __init__(self, parent):
        self.player = parent
        X=np.loadtxt('AWS_collapsed.txt')
        X = (X+1)/2
        Freq=np.zeros(100)
        #
        for i in X:
            Freq[int(np.ceil(i*100))]+=1
        #
        X=np.linspace(0,1,100)
        #
        with pm.Model():
            # Priors are posteriors from previous iteration
            alpha = Normal('alpha', 0.5,0.5)
            beta = Normal('beta', 0.5,0.5)
            gamma = Normal('gamma',0.5,0.5)
            delta = Normal('delta',0.5,0.5)

        # self.trace = initialise_prior(X,Freq)
            self.trace = pm.backends.text.load('AWS')

if __name__ == "__main__":

    game = GameState(n_human_players=1, n_ai_players=1, n_cards=10)

    q = game.pop_q()

    print("Current questions:", game.current_question)

    print("Human cards:")
    print(game.human_players[0].player.display_cards())

    blanks = q.count("_")
    if blanks == 1:
        phrase = q.replace("_", game.human_players[0].player.card_strings[2][:-1])
    elif blanks == 0:
        print("Can only handle blanks")
        print("Not: " + q )
        sys.exit()
    else:
        print("Not ready!")
        print("Question too many _ : " + q)
        sys.exit()

    print("Random Phrase:")
    print(phrase)
    sys.exit()
    print("azure analysis:")
    print(azure_sentiment_score(phrase))

    print("amazon analysis:")
    print(amazon_sentiment_score(phrase))

    print("google analysis:")
    # print(google_sentiment_score(phrase))
