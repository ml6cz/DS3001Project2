#DS 3002 Project 2 - Megan Lin & Diana Albarracin
import tweepy
import logging
import time
import re
import os
import openweathermapy.core as owm
import requests, json
import datetime

import random

twitter_keys = {
        'CONSUMER_KEY':'CtUaQjfgbdoMreAyv0lSF76EM',
        'CONSUMER_SECRET':     'lEOvHrpJDDwZHrCPLMxGxq8NTEV7svhsWwBNVA0Ebm8WOUGevs',
        'BEARER_TOKEN': "AAAAAAAAAAAAAAAAAAAAAOYEGwEAAAAAkUx%2BYi8MuFAj6WIphXJTpg4zpzo%3DOX3y3Eq4FR0DrX2l3F8kG2oVuab8GNyUS9ChgejUdtthy1Tb6l",
        'ACCESS_TOKEN': '2314692336-SLdDrLWF0hJw3Udc4X3d3zc4MieHz6bkwFztJrh',
        'ACCESS_TOKEN_SECRET': 'msNo3cQn57HMMCsm5mxWWKUiSIsI8KiWymrRkOitoUUIK'
    }

# Authenticate to Twitter
auth = tweepy.OAuthHandler(twitter_keys['CONSUMER_KEY'], twitter_keys['CONSUMER_SECRET'])
auth.set_access_token(twitter_keys['ACCESS_TOKEN'], twitter_keys['ACCESS_TOKEN_SECRET'])

# Create API object
api = tweepy.API(auth)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def tweetReply(api, new_since_id):
    tweet = api.get_status(new_since_id)
    
    # Extract the zipcode
    us_zip = r'(\d{5}\-?\d{0,4})'
    zip_code = re.search(us_zip, tweet.text)
    if type(zip_code) is not type(None):
        zipcode = zip_code.group(1)
        
        # Take the zipcode, and pass it through the OpenWeatherMap API (https://openweathermap.org/api)
        api_key = "092cffc85ccc6db7d505a7c85f1d0fac"
        base_url = "http://api.openweathermap.org/data/2.5/weather?"
        #query the API using our unique API key and
        complete_url = base_url + "appid=" + api_key + "&zip=" + str(zipcode) + ",US"+"&units=imperial"
        
        
        response = requests.get(complete_url)
        x = response.json()
        
        # When the Code is 200, the API has succeeded in finding the weather info for the zipcode
        if x["cod"] == 200:
            ct = datetime.datetime.now()
                    
            response = "\nFeels Like: " + str(x["main"]["temp"]) + " deg F"
            response += "\nHumidity: " + str(x["main"]["humidity"])
            response += "\nDescription: " + x["weather"][0]["description"]
            response +="\n\n(Checked at:"+str(ct)+")"
            
            response = x["name"] + "("+str(zipcode)+") currently\n"+response
                    
            api.update_status(status = response,in_reply_to_status_id=new_since_id)
            print(response)
        
        # When the Code is 404, that means that an invalid zipcode has been entered
        elif x["cod"] == 404:
            ct = datetime.datetime.now()
            response = "No valid zipcode found in: "+tweet.text[11:] +"\n\n(Checked at:"+str(ct)+")"
            print("Error 404: " + response)
            api.update_status(status = response, in_reply_to_status_id=new_since_id)
            
        # There are a lot of other codes, so we will return a general error message
        else:
            ct = datetime.datetime.now()
            response = "Unknown error found in: "+tweet.text[11:] +"\n\n(Checked at:"+str(ct)+")"
            print("Error "+str(x["cod"])+": " + response)
            api.update_status(status = response, in_reply_to_status_id=new_since_id)
            
                    
    else:
        ct = datetime.datetime.now()
        response = "No valid zipcode found in: "+tweet.text[11:] +"\n\n(Checked at:"+str(ct)+")"
        api.update_status(status = response, in_reply_to_status_id=new_since_id)
        print("Regex Error: " + response)
                
    
def check_mentions(api, keywords, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id).items():
        #get the most recent tweet based on the largest tweet ID in the user's timeline
        new_since_id = max(tweet.id, new_since_id)
        
        #if the tweet has not been replied to yet
        if tweet.in_reply_to_status_id is not None:
            continue
        
        #tweet info to the user how the Twitterbot works
        if any(keyword in tweet.text.lower() for keyword in ["info", "help"]):
            logger.info(f"Giving help to {tweet.user.name}")
            logger.info(tweet.text)
            api.update_status(status = "Tweet me with a zipcode and I'll give you a realtime summary of weather in the area!\n\nJust use any of the following keyphrases: temperature, weather, how is it in, check",in_reply_to_status_id=new_since_id)
        
        #if a keyword regarding weather is found, then tweet a reply
        elif any(keyword in tweet.text.lower() for keyword in keywords):
            logger.info(f"Answering to {tweet.user.name}")
            logger.info(tweet.text)
            tweetReply(api, new_since_id)

    return new_since_id

def main():
    since_id = 22126889
    
    while True:
        since_id = check_mentions(api, ["temperature", "weather", "how is it in", "check"], since_id)
        logger.info("Waiting...")
        time.sleep(60)

if __name__ == "__main__":
    main()