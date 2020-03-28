import logging

import azure.functions as func
import os
import tweepy


def main(msg: func.ServiceBusMessage):
    twitter_key = os.environ['TwitterAPIKey']
    twitter_secret = os.environ['TwitterAPISecret']
    twitter_access_token = os.environ['TwitterAccessToken']
    twitter_access_token_secret = os.environ['TwitterAccessTokenSecret']

    # Setup auth
    twitter_auth = tweepy.OAuthHandler(twitter_key, twitter_secret)
    twitter_auth.set_access_token(twitter_access_token, twitter_access_token_secret )

    # Create twitter API object
    tweeter = tweepy.API(twitter_auth)

    # Tweet message
    body_content = msg.get_body().decode('utf-8')
    tweeter.update_status(body_content)
    logging.info('Python ServiceBus queue trigger processed message: %s',
             msg.get_body().decode('utf-8'))
