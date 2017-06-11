import tweepy
import re

class TweetAnalyzer(object):

	def __init__(self,tweet=None):
		
		self.__tweet = tweet

	def getAllHashtags(self):
		
		# search for all hashtags in a tweet
		# get tweet text
		tweetTxt = self.__tweet.text

		# search for hashtags
		pattern = "#\w*"
		hashtags = [x.lower() for x in re.findall(pattern,tweetTxt)]
		return hashtags

	def setTweet(self,tweet):
		self.__tweet = tweet


