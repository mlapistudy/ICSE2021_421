# Sentiment Analysis of Stocks
# Written by: Adithya Ramanathan, Rishi Bhuta, Daniel Verderese

# Libraries
######################################################################

# RSS parsing
import feedparser

# HTML tag parsing
from HTMLParser import HTMLParser

# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types


# Classes
######################################################################

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


# Functions
######################################################################

# Removes html tags
def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

# Iterates through RSS feeds and creates a list of dicts:
# dict: {headline, url, tickers, lowercase_headline}
def create_mentions_list(url_list):
  mentions = []

  for url in url_list:
    feed = feedparser.parse( url )['entries']

    for item in feed:
      mentioned_stocks = []

      if 'tags' in item:
        for ticker in item['tags']:
          mentioned_stocks.append(ticker['term'])
      
      
      
      url = ""
      headline = ""

      # Coming from CNN
      if 'feedburner_origlink' in item:
        url = item['feedburner_origlink']
        headline = item['title']
        headline = strip_tags(headline)
      elif 'summary_detail' in item:
        url = item['links'][0]['href']
        headline = item['summary_detail']['value']
        headline = strip_tags(headline)

      else:
        continue


      item_dict = {}
      item_dict['url'] = url
      item_dict['headline'] = headline
      item_dict['tickers'] = mentioned_stocks
      item_dict['lowercase_headline'] = headline.lower()

      mentions.append(item_dict)

  return mentions

# Checks headlines for mention of specified company
def headline_check(mentions_list, company):
  relevant_headlines = []
  relevant_urls = []
  for i in mentions_list:
    if company in i['lowercase_headline']:
      if i['headline'] not in relevant_headlines:
        relevant_headlines.append(i['headline'])
        relevant_urls.append(i['url'])

  return relevant_headlines, relevant_urls

# Checks headlines/tickers for mention of specified ticker
def ticker_check(mentions_list, ticker):
  relevant_headlines = []
  relevant_urls = []
  for i in mentions_list:
    if ticker in i['tickers']:
      if i['headline'] not in relevant_headlines:
        relevant_headlines.append(i['headline'])
        relevant_urls.append(i['url'])

  return relevant_headlines, relevant_urls

# Returns a verbal evaluation of sentiment based on a given average
def sentiment_range(avg):
  if avg < -.8:
    return "Definetly Negative"
  elif avg < -.55:
    return "Very Negative"
  elif avg < -.25:
    return "Negative"
  elif avg < -.05:
    return "Slightly Negative"
  elif avg < .05:
    return "Neutral"
  elif avg < .25:
    return "Slightly Positive"
  elif avg < .55:
    return "Positive"
  elif avg < .8:
    return "Very Positive"
  else:
    return "Definetly Positive"

# Detects the sentiment for a conglomeration of headlines for a given stock
def detect_sentiment(text, stock):


  # Instantiates a client
  client = language.LanguageServiceClient()

  # The text to analyze
  document = types.Document(
      content=text,
      type=enums.Document.Type.PLAIN_TEXT)

  # Detects the sentiment of the text
  response = client.analyze_sentiment(document=document)

  

  entities = response.sentences
  overall_sentiment = response.document_sentiment

  # print('Document Sentiment: {}'.format(overall_sentiment.score))

  # score range:
  # -1.0 to -.25 = negative
  # -.25 to .25 = neutal
  # .25 to 1 = positive
  neg_count = 0
  pos_count = 0
  neutral_count = 0
  total = 0.0
  count = 0.0
  for entry in entities:
    score = entry.sentiment.score
    total += score
    count += 1.0
    if score <= -.25:
      neg_count += 1
    elif -.25 < score < .25:
      neutral_count += 1
    else:
      pos_count += 1
  avg = 0
  if total != 0:
    avg = float(total/count)
  sentence_sentiment = sentiment_range((avg))

  return ("For the stock {}, the outlook is {}").format(stock, sentence_sentiment)

# Creates list of RSS urls for the tickers specified in input list
def create_company_urls(ticker_list):
  urls = []
  for ticker in ticker_list:
    custom_url = "http://markets.financialcontent.com/stocks/action/rssfeed?Symbol=" + str(ticker)
    urls.append(custom_url)

  return urls

# "Main" function. Takes in user input for stock and company name
#   - Uses input to derive sentiment
def main():

  # RSS URLS
  investopedia_gen_news_url = 'http://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_stock_analysis'
  investopedia_stock_news_url = "http://www.investopedia.com/feedbuilder/feed/getfeed/?feedname=rss_stock_analysis"
  cnn_money_latest_url = "http://rss.cnn.com/rss/money_latest.rss"
  cnn_companies_url = "http://rss.cnn.com/rss/money_news_companies.rss"
  cnn_markets_url = "http://rss.cnn.com/rss/money_markets.rss"

  ticker = raw_input("Please enter the ticker for your desired stock:\n")
  
  stock_name = raw_input("Please enter the company name for your desired stock:\n")

  ticker = ticker.upper()
  stock_name = stock_name.lower()

  ticker_list = [ticker]

  company_urls = create_company_urls(ticker_list)


  url_list = [investopedia_gen_news_url, investopedia_stock_news_url, cnn_money_latest_url, cnn_companies_url, cnn_markets_url]
  url_list = url_list + company_urls


  mentions = create_mentions_list(url_list)

  relevant_headlines_ticker, relevant_urls_ticker = ticker_check(mentions, ticker)
  relevant_headlines_company, relevant_urls_company = headline_check(mentions, stock_name)

  text = ""
  bad_headline_count = 0
  if len(relevant_headlines_company) > 0:
    # print ("Relevant headlines: ")
    for headline in relevant_headlines_company:
      # print headline
      try: 
        newline = str(headline) + "\n"
        text += newline
      except:
        # do nothing
        bad_headline_count += 1

  print detect_sentiment(text, stock_name)


# MAIN
######################################################################


if __name__ == "__main__":
    main()
