import os
import sys
import tweepy
import requests
# import pandas as pd

UTIL_PATH = os.getcwd() + "/../"
sys.path.append(UTIL_PATH)
import util
from util import tweetManager as twitMng
from util import accountManager as accMng

META_PATH = os.getcwd() + "/meta/"
LOG_PATH = os.getcwd() + "/logs/"



def getAuthData():
	with open(META_PATH + "auth.dat",'r') as inp:
		conKey, conSec, accKey, accSec  =\
		 inp.readline().strip().split(",")

	return conKey, conSec, accKey, accSec


def getAPI():
	# some boring code to authenticate bot
	consumerKey, consumerSec, accessKey, accessSec = getAuthData()
	auth = tweepy.OAuthHandler(consumerKey, consumerSec)

	auth.set_access_token(accessKey,accessSec)
	api = tweepy.API(auth)

	return api


def retweetAtweet(api):

	# look for a tweet with certain # and retweet it
	tweetManager = twitMng.TweetManager(api=api)
	tweetManager.findTweets(followUser=True,favorCutOff=10,retweetCutOff=10)


def manageAccount(api):

	# manage my account!
	accountManager = accMng.AccountManager(api)
	accountManager.followSomeFans(followProb=0.05)

def main():

	# get tweepy API
	api = getAPI()

	# retweet somebody!
	retweetAtweet(api)
	
	# manage my fans (or account)
	manageAccount(api)



if __name__ == '__main__':
	main()