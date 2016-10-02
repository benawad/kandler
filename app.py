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
import regex as re
import pandas.io.data as web

app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello!'

@app.route("/webhook", methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        # loop through unread messages
        for m in data['entry'][0]['messaging']:
            if 'message' in m:
                symbol = m['message']['text']
            if re.match("follow\s(.*?)(.*?)\-(.*?)\s(.*?)$", symbol):
                for x in re.finditer(r"\w+",symbol):
                    print(x)
                    if re.match("^[0-9]$",x.group()):
                        nmin=x.group()
                    elif re.match("^[A-Z]{1,4}$",x.group()):
                        ticker=x.group()
                print("You will now get updates on "+ticker+" every "+nmin +" minutes")
            elif re.match("follow\s(.*?)(.*?)\-(.*?)\s(.*?)$", symbol):
                for x in re.finditer(r"\w+",symbol):
                    print(x)
                    if re.match("^[A-Z]{1,4}$",x.group()):
                        ticker=x.group()
                print("You will now get updates on "+ticker+" every 1 minute")
            elif re.match("^[A-Z]{1,4}$",symbol):
                for k, v in ystockquote.get_all(symbol).items():
                    send_message(m['sender']['id'], "%s: %s" % (k, v))
                try:
                    send_picture(m['sender']['id'], symbol)
                except:
                    pass
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

if __name__ == "__main__":
    app.run()
