import os
import tweepy
import pandas as pd
from time import sleep
from random import randint

META_PATH = os.getcwd() + "/meta/"
RETWEET_LOG_PATH = os.getcwd() + "/log/"
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


	def __readTags(self):

		# read hashtag file
		with open(META_PATH + "hashTags.dat",'r') as file:
			for line in file:
				self.__tags.append(line.strip())


	def findTweets(self,followUser=False,favorCutOff=None,retweetCutOff=None):
		
		# set favroCutOff and retweetCutoff
		self.__favorCutOff = favorCutOff
		self.__retweetCutOff = retweetCutOff
		# read hastTags
		self.__readTags()
		# select a random tag
		tag = "#" + self.__tags[randint(0,len(self.__tags)-1)]
		# retweet a popular tweet with this tag and follow the
		# user if applicable
		print("Looking for tag " + tag)
		print()
		# look for a valid tweet to retweet it!
		while True:

			selectedTweet = None

			for tweet in self.__errorHandler\
			(tweepy.Cursor(self.__api.search,q=tag,lang="en").items()):
				# sanity check
				print("Processing tweet of user: @" + str(tweet.user.screen_name))
				
				# process tweet
				selectedTweet = self.__processTweet(tweet,tag)
				if not selectedTweet:
					continue

				if self.__retweetDone:
					print("Tweet Successfully retweeted!!")
					break
			
			# check if user should be followed
			if followUser:
				self.__followUser(selectedTweet.user.id)
			break


	def __processTweet(self,tweet,tag):

		# some cut-off vals
		userFollowerCutOff = randint(0,1000) + 300

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
				self.__updateRetweetLog(tweet,tag)
				print("Tweet data was saved to retweet log file!")
				# favor it with a low chance
				if not tweet.favorited:
					self.__favorTweetWithLowChance(tweet)

				self.__retweetDone = True
				return tweet

			except tweepy.TweepError:
				# print(e.cause)
				return None

		else:
			return None



	def __updateRetweetLog(self,tweet,tag):

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
				t = self.__getTweetMetaData(tweet,tag)
				df = df.append(t)
				# save new retweetLog
				df.to_csv(retweetFile,sep=",")

		# if no retweet file is found then create it
		else:
			t = self.__getTweetMetaData(tweet,tag)
			t.to_csv(retweetFile,sep=",")


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


