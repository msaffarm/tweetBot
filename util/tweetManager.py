import os
import tweepy
from time import sleep
from random import randint
META_PATH = os.getcwd() + "/meta/"


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
		print
		# look for a valid tweet to retweet it!
		while True:

			selectedTweet = None

			for tweet in self.__errorHandler\
			(tweepy.Cursor(self.__api.search,q=tag,lang="en").items()):
				# sanity check
				print("Processing tweet of user: @" + str(tweet.user.screen_name))
				
				# process tweet
				selectedTweet = self.__processTweet(tweet)
				if not selectedTweet:
					continue

				if self.__retweetDone:
					print("Tweet Successfully retweeted!!")
					break
			
			# check if user should be followed
			if followUser:
				self.__followUser(selectedTweet.user.id)
			break


	def __processTweet(self,tweet):

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
		if tweet.favorite_count > 10:
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


