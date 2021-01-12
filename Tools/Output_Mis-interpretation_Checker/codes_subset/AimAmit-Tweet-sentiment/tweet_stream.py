import os
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta

import tweepy as tw
from google.cloud import language
from google.cloud.language import enums, types
from nltk.tokenize import WordPunctTokenizer
from telegram.ext import Filters, MessageHandler, Updater

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv('dir_to_google_creds')
consumer_key = os.getenv('consumer_key')
consumer_secret = os.getenv('consumer_secret')
access_token = os.getenv('access_token')
access_token_secret = os.getenv('access_token_secret')
telegram_api = os.getenv('telegram_access_api')

project = os.getenv('project')
pubsub_topic = os.getenv('pubsub_topic')

# publisher = pubsub_v1.PublisherClient()
# topic_path = publisher.topic_path(project,  pubsub_topic)


def create_api():
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True,
                 wait_on_rate_limit_notify=True)
    try:
        api.verify_credentials()
    except Exception as e:
        # print("Error creating API")
        raise e
    # print("Twitter API created")
    return api


def search_tweets(keyword, total_tweets):
    # today_datetime = datetime.today().now()
    # yesterday_datetime = today_datetime - timedelta(days=1)
    # today_date = today_datetime.strftime('%Y-%m-%d')
    # yesterday_date = yesterday_datetime.strftime('%Y-%m-%d')

    search_result = tw.Cursor(api.search,
                              q=keyword + "  -filter:retweets",
                              #   since=yesterday_date,
                              result_type='recent',
                              tweet_mode="extended",
                              lang='en').items(total_tweets)
    return search_result


def clean_tweets(tweet):
    BLANK = 0
    # print(tweet)
    tweet = re.sub(r'[\t\r\n]', ' ', tweet)
    tweet = re.sub(r'\w*\d\w*', '', tweet)
    tweet = re.sub(r'[@#]\w+', '', tweet, flags=re.MULTILINE)

    tweet = re.sub('https?://[A-Za-z0-9./]+', '', tweet, flags=re.MULTILINE)
    tweet = tweet.lower()
    tweet = re.sub('[^a-zA-Z]', ' ', tweet, flags=re.MULTILINE)
    tweet = re.sub('[$₹]', '', tweet, flags=re.MULTILINE)

    tok = WordPunctTokenizer()
    words = tok.tokenize(tweet)
    tweet = (' '.join(words)).strip()
    if not tweet:
        BLANK = 1
    return tweet, BLANK


def get_sentiment_score(tweet):
    client = language.LanguageServiceClient()
    document = types\
        .Document(content=tweet,
                  type=enums.Document.Type.PLAIN_TEXT)
    sentiment_score = client\
        .analyze_sentiment(document=document)\
        .document_sentiment\
        .score
    return sentiment_score


def analyze_tweets(keyword, total_tweets):
    score = 0
    blank = 0
    tweets = search_tweets(keyword, total_tweets)
    for tweet in tweets:
        tweet = tweet.full_text
        # print(tweet)
        cleaned_tweet, isblank = clean_tweets(tweet)
        # print('Tweet: {}'.format(cleaned_tweet))
        blank += isblank
        # print(cleaned_tweet, end='\n\n')
        sentiment_score = get_sentiment_score(cleaned_tweet)
        score += sentiment_score

        # print('Score: {}\n'.format(sentiment_score))
    final_score = round((score / float(total_tweets-blank)), 2)
    # print('Final Score : ', final_score, end='\n\n')
    return final_score


def send_the_result(bot, update):
    keyword = update.message.text
    # print(keyword)
    final_score = analyze_tweets(keyword, 10)
    if final_score <= -0.25:
        status = 'NEGATIVE ❌'
    elif final_score <= 0.25:
        status = 'NEUTRAL 🔶'
    else:
        status = 'POSITIVE ✅'
    bot.send_message(chat_id=update.message.chat_id,
                     text='Average score for '
                     + str(keyword)
                     + ' is '
                     + str(final_score)
                     + ' '
                     + status)


if __name__ == "__main__":

    global api
    api = create_api()

    updater = Updater(telegram_api)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, send_the_result))
    updater.start_polling()
    updater.idle()
