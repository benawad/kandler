from flask import Flask, request
import json
import requests
import os
import plotly
from imgurpython import ImgurClient
import plotly.plotly as py
from plotly.tools import FigureFactory as FF
from datetime import datetime
import ystockquote
import plotly.graph_objs as go
import re
import pandas.io.data as web
import tweepy

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

def valid_input(symbol):
    return re.match("^[A-Z]{1,5}$", symbol)

def news(recipient_id, symbol):
    pass

def twitter(recipient_id, symbol):

    consumer_key=os.environ['T_CONSUMER_KEY']
    consumer_secret=os.environ['T_CONSUMER_SECRET']
    access_token_key=os.environ['T_ACCESS_TOKEN_KEY']
    access_token_secret=os.environ['T_ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token_key, access_token_secret)

    api = tweepy.API(auth)

    results = api.search(q="$"+symbol, count=5, include_entities=True)
    for i in results:
        twitter_thumbnail(recipient_id, results)

@app.route("/webhook", methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        data = request.get_json()
        # loop through unread messages
        for m in data['entry'][0]['messaging']:
            if 'postback' in m:
                payload = m['postback']['payload']
                payload = payload.split("|")
                if payload[0] == "twitter":
                    twitter(m['sender']['id'], payload[1])
                elif payload[0] == "data":
                    sym_data = ystockquote.get_all(payload[1])
                    for k, v in sym_data.items():
                        send_message(m['sender']['id'], "%s: %s" % (k, v))
                elif payload[0] == "news":
                    news(m['sender']['id'], payload[1])
                else:
                    send_message(m['sender']['id'], "Please enter a symbol like AAPL")
            if 'message' in m:
                symbol = m['message']['text']
                symbol = symbol.strip().upper()
                if not valid_input(symbol):
                    send_message(m['sender']['id'], "Please enter a symbol like AAPL")
                else:
                    try:
                        # send_picture(m['sender']['id'], symbol)
                        pass
                    except Exception as e:
                        print("ERROR")
                        print(e)
                    price = ystockquote.get_price(symbol)
                    if "N/A" == price:
                        send_message(m['sender']['id'], "Unknown symbol")
                        send_message(m['sender']['id'], "Please enter a symbol like AAPL")
                    else:
                        send_thumbnail(m['sender']['id'], symbol, price)

        return "ok!", 200
    else:
        token = request.args.get('hub.verify_token', '')
        mode = request.args.get('hub.mode', '')
        challenge = request.args.get('hub.challenge', '')
        correct_token = os.environ['VERIFY_TOKEN']

        if token == correct_token and mode == 'subscribe':
            return challenge, 200
        else:
            return "Something went wrong :(", 403

def twitter_thumbnail(recipient_id, result):
    if not hasattr(result, 'text'):
        return
    link = ""
    if hasattr(result, 'entities'):
        if 'media' in result.entities:
            link = result.entities['media'][0]['expanded_url']
        elif 'urls' in result.entities:
            link = result.entities['urls'][0]['expanded_url']
    element = {
                "title": result.text,
                "subtitle": "%s on %s" % (result.user.name, result.created_at),
            }
    if link:
        element["item_url"] = link
    message_data = {
        'recipient': {'id': recipient_id},
        'message': {
            "attachment":{
              "type":"template",
              "payload":{
                "template_type":"generic",
                "elements":[
                    element
                ]
              }
            }
        }
    }
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(message_data))
    if r.status_code == 200:
        print('Sent "%s" to %s' % (recipient_id, message_data))
    else:
        print('FAILED to send "%s" to %s' % (recipient_id, message_data))
        print('REASON: %s' % r.text)

def send_message(recipient_id, message):
    message_data = {
        'recipient': {'id' : recipient_id},
        'message': {'text' : message}
    }
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(message_data))
    if r.status_code == 200:
        print('Sent "%s" to %s' % (recipient_id, message))
    else:
        print('FAILED to send "%s" to %s' % (recipient_id, message))
        print('REASON: %s' % r.text)

def upload_image_to_imgur(path):
    client_id = os.environ['IMGUR_CLIENT_ID']
    client_secret = os.environ['IMGUR_CLIENT_SECRET']


    client = ImgurClient(client_id, client_secret)
    url = client.upload_from_path(path)
    return url['link']


def make_candlechart(symbol):
    plotly.plotly.sign_in(username='benawad', api_key=os.environ['PLOTLY_KEY'])
    df = web.DataReader(symbol, 'yahoo', datetime(2016, 9, 1), datetime(2016, 9, 30))
    fig = FF.create_candlestick(df.Open, df.High, df.Low, df.Close, dates=df.index)
    fig['layout'] = go.Layout(title=symbol)
    py.image.save_as(fig, filename='tgraph.png')


def send_picture(recipient_id, symbol):
    make_candlechart(symbol)
    img_url = upload_image_to_imgur("tgraph.png")
    print(img_url)

    message_data = {
        'recipient': {'id': recipient_id},
        'message': {
            'attachment': {
                "type": "image",
                "payload": {
                        "url": img_url,
                    }
                }
            }
        }
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(message_data))
    if r.status_code == 200:
        print('Sent "%s" to %s' % (recipient_id, img_url))
    else:
        print('FAILED to send "%s" to %s' % (recipient_id, img_url))
        print('REASON: %s' % r.text)
def news(symbol):
    url = "https://access.alchemyapi.com/calls/data/GetNews?apikey=8a13813889288f9c8c1de42996bf0a3626559e52&return=enriched.url.title,enriched.url.url,enriched.url.publicationDate,enriched.url.enrichedTitle.docSentiment&start=1472774400&end=1475449200&q.enriched.url.enrichedTitle.entities.entity=|text="+symbol+",type=company|&count=10&outputMode=json"
    req = requests.get(url)
    r = json.loads(req.content)
    for x in r['result']['docs']:
        sentimentType = x['source']['enriched']['url']['enrichedTitle']['docSentiment']['type']
        sentiment = x['source']['enriched']['url']['enrichedTitle']['docSentiment']['score']
        if sentimentType=="positive":
            negativeSentiment=round(abs(sentiment)*100)
            positiveSentiment=1-negativeSentiment
        elif sentimentType=="negative":
            positiveSentiment=round(abs(sentiment)*100)
            negativeSentiment=1-positiveSentiment

        publicationDate= x['source']['enriched']['url']['publicationDate']['date']
        try:
            monthDate = re.search("2016(.+?)T(.+?)",publicationDate).group(1)
        except AttributeError:
            monthDate=''
            
        title=x['source']['enriched']['url']['title']
        
        url=x['source']['enriched']['url']['url']

        listVal=[sentimentType,sentiment,monthDate,title,url]
        return listVal


def send_thumbnail(recipient_id, symbol, price):
    message_data = {
        'recipient': {'id': recipient_id},
        'message': {
            "attachment":{
              "type":"template",
              "payload":{
                "template_type":"generic",
                "elements":[
                  {
                    "title":symbol,
                    "subtitle": "Price: %s" % price,
                    "buttons":[
                      {
                        "type":"postback",
                        "title":"More data",
                        "payload": "data|%s" % symbol,
                      },
                      {
                        "type":"postback",
                        "title":"News",
                        "payload": "news|%s" % symbol,
                      },
                      {
                        "type":"postback",
                        "title":"Tweets",
                        "payload": "twitter|%s" % symbol,
                      },
                    ]
                  }
                ]
              }
            }
        }
    }
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=json.dumps(message_data))
    if r.status_code == 200:
        print('Sent "%s" to %s' % (recipient_id, message_data))
    else:
        print('FAILED to send "%s" to %s' % (recipient_id, message_data))
        print('REASON: %s' % r.text)

if __name__ == "__main__":
    app.run()
