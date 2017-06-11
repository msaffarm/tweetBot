import os
import sys
import tweepy
import pandas as pd
from time import sleep
from random import randint, sample

CURRENT_DIR =  os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURRENT_DIR)
from tweetAnalyzer import TweetAnalyzer

META_PATH = CURRENT_DIR + "/../meta/"
RETWEET_LOG_PATH = CURRENT_DIR + "/../log/"
RETWEET_LOG_FILE = "retweetLog.csv"


class TweetManager(object):
	"""
	A tweet manager to track tweet with certain #s 
	and follow the tweet user!
	"""

	def __init__(self,api=None):

		self.__api = api
		# self.__tweetInfo = {}
		# self.__tweet = tweet
		self.__retweetDone = False
		self.__tags = []



	def __chooseHashtagsRandom(self,numOfTags=2):
		
		# read hashtag file
		allTags = []
		with open(META_PATH + "hashTags.dat",'r') as file:
			for line in file:
				allTags.append(line.strip())

		# randomly select hashtags from hashTags.dat file

		selectedTagsIdx = sample(range(len(allTags)),numOfTags)
		# empty tags list in case of repetitice calls to this 
		# function
		self.__tags = []

		for index in selectedTagsIdx:
			self.__tags.append("#" + allTags[index])

		# print tags
		print("Looking for tag(s) " + str(self.__tags))
		print()



	def findTweets(self,chooseRandomHashtags=True,searchHashtags=None,**kwargs):
		
		# process arguments
		args = kwargs.keys()
		if "followUser" not in args:
			kwargs["followUser"] = False
		if "favorCutOff" not in args:
			kwargs["favorCutOff"] = 5
		if "retweetCutOff" not in args:
			kwargs["retweetCutOff"] = 5
		if "numberOfRandomHashtags" not in args:
			kwargs["numberOfRandomHashtags"] = 1

		# set favroCutOff and retweetCutoff
		self.__favorCutOff = kwargs["favorCutOff"]
		self.__retweetCutOff = kwargs["retweetCutOff"]
		
		# choose hashtags to search for!
		if chooseRandomHashtags:
			# choose random hashtags hastTags
			self.__chooseHashtagsRandom(numOfTags=kwargs["numberOfRandomHashtags"])
		else:
			self.__tags = searchHashtags
			print("Looking for tag(s) " + str(self.__tags))
			print()
		
		# retweet a popular tweet with this tag and follow the
		# user if applicable
		# instanciate a tweet analyzer
		ta = TweetAnalyzer()

		# counter to keep track of tweets analyzed for give hashtags!
		# This is useful since some combinations of hashtags are hard
		# to find 
		tweetsProcessedThresh = 500

		# look for a valid tweet to retweet it!
		while True:

			selectedTweet = None
			processedTweetCounter = 0

			for tweet in self.__errorHandler\
			(tweepy.Cursor(self.__api.search,q=self.__tags[0],lang="en")\
				.items(tweetsProcessedThresh+1)):
				
				# check if threshold is passed
				if processedTweetCounter > tweetsProcessedThresh:
					self.__chooseHashtagsRandom(numOfTags=\
						kwargs["numberOfRandomHashtags"])
					processedTweetCounter = 0


				# sanity check
				print("Processing tweet of user: @" + str(tweet.user.screen_name))
				
				# process tweet
				ta.setTweet(tweet)
				try:
					selectedTweet = self.__processTweet(tweet,ta)
				except tweepy.RateLimitError:
					print("Tweepy Rate Limit Error Reached!")
					sleep(5*60)
					continue


				if not selectedTweet:
					# increment processedTweetCounter
					processedTweetCounter += 1
					continue

				if self.__retweetDone:
					print("Tweet Successfully retweeted!!")
					break

			# In some combinations of hashtags there
			# is no returned value in api.search and 
			# selectedTweet will be None.
			if not selectedTweet:
				print("No tweet with " + str(self.__tags) + " was found!")
				self.__chooseHashtagsRandom(numOfTags=\
					kwargs["numberOfRandomHashtags"])
				continue

			# check if user should be followed
			if kwargs["followUser"]:
				self.__followUser(selectedTweet.user.id)
			break


	def __processTweet(self,tweet,ta):

		# some cut-off vals
		userFollowerCutOff = randint(0,1000) + 100

		# determine whether to follow the user of not
		userId = tweet.user.id
		retwitCount = tweet.retweet_count
		favorCount = tweet.favorite_count
		userFollowerCount = tweet.user.followers_count

		# is it me?!
		if self.__api.me().screen_name==userId:
			return None

		# is already retweeted!
		if tweet.retweeted:
			return None

		# check if tweet has all the selected tags
		tweetTags = ta.getAllHashtags()
		for tag in self.__tags:
			if tag not in tweetTags:
				return None
		# # if reached here then it has all the tags
		# hasAllTags = True


		# check if tweet is popular
		isPopular = False
		# tweet stats
		if retwitCount>=self.__favorCutOff and favorCount>=self.__favorCutOff:
			isPopular = True
		# is user popular (user stats)
		if userFollowerCount < userFollowerCutOff:
			isPopular = False

		# if tweet is popular then retweet it, else return
		if isPopular:
			# retweet it
			try:
				tweet.retweet()
				# update retweet log
				self.__updateRetweetLog(tweet)
				print("Tweet data was saved to retweet log file!")
				# favor it with a low chance
				if not tweet.favorited:
					self.__favorTweetWithLowChance(tweet)

				self.__retweetDone = True
				return tweet

			except:
				# print(e.cause)
				return None

		else:
			return None



	def __updateRetweetLog(self,tweet):

		# update the retweet metaData
		retweetFile = RETWEET_LOG_PATH + RETWEET_LOG_FILE

		# if retweetLog file already exists then update it
		if os.path.lexists(retweetFile):
			# open it and update it
			df = pd.read_csv(retweetFile)
			tweeetUserId = tweet.user.id
			# check if user has been retweeted already! 
			if any(df["user ID"].isin([tweeetUserId])):
				df[df["user ID"]==tweeetUserId]["user retweeted count"] += 1
			else:
				# new user is retweeted! update the log accordingly!
				tags = ",".join(self.__tags)
				t = self.__getTweetMetaData(tweet,tags)

				# # sanity check
				# print(t.to_string())
				# print(df.to_string())

				df = df.append(t)
			
			# save new retweetLog
			df.to_csv(retweetFile,sep=",",index=False)

		# if no retweet file is found then create it
		else:
			tags = ",".join(self.__tags)
			t = self.__getTweetMetaData(tweet,tags)
			t.to_csv(retweetFile,sep=",",index=False)


	def __getTweetMetaData(self,tweet,tag):

		# dataframe columns
		cols = ["user ID","user screen name",\
		"user retweeted count","user follower count","tweet tag",\
		"tweet favors", "tweet retweets"]

		# get user
		user = tweet.user
		
		# dataframe values
		vals = [user.id,user.screen_name,1,user.followers_count,tag,\
		tweet.favorite_count,tweet.retweet_count]

		# append this data to dataframe
		t = pd.DataFrame([vals],columns=cols)

		return t


	def __followUser(self,userId):

		# check if user is already followed
		if self.__isUserFriend(userId):
			print("User already is a friend!")
		else:
			user = self.__api.get_user(id=userId)
			user.follow()
			print("User was followed successfully!")


	def __isUserFriend(self,userId):
	
		# get my info
		myFreinds = self.__api.friends_ids(self.__api.me().screen_name)
		return userId in myFreinds


	def setAPI(self,api):
		self.__api = api


	def __favorTweetWithLowChance(self,tweet):

		# favor the tweet with low chance!
		# if tweet is popular then like it
		if tweet.favorite_count > 30:
			tweet.favorite()
			print("Tweet was liked!")

		# if not so popular then give it a chance!
		rand = randint(0,10)
		if rand < 1:
			tweet.favorite()
			print("Tweet was liked!")


	def __errorHandler(self,cursor):
		while True:
			try:
				yield cursor.next()

			except tweepy.RateLimitError:
				print("Rate limit error!")
				sleep(10*60)

			except tweepy.TweepError:
				sleep(5)


