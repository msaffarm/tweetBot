import tweepy
from random import randint


class AccountManager(object):

	def __init__(self,api=None):		
		self.__api = api


	def followAllFans(self):
		
		# get my fans and friends
		myFriends, myFollowers = self.__getFansAndFollowers()

		# follow all of my fans (Not realistic, I know)
		for fan in myFollowers:
			if fan not in myFriends:
				self.__followUser(self,fan)


	def followSomeFans(self,followProb=None):
		
		# A more realistic implementation of followAllFans!

		# get my fans and friends
		myFriends, myFollowers = self.__getFansAndFollowers()

		# follow each of them with some probabilty
		if not followProb:
			followProb = 0.1

		for fan in myFollowers:
			if fan not in myFriends:
				self.__followWithChance(fan,followProb)
				

	def __followWithChance(self,userID,followProb):
		
		# generate a random number in (0,100)
		rand = randint(0,100)
		if rand < followProb*100:
			self.__followUser(userID)


	def __followUser(self,userID):

		# follow user only if it has more than 200 followers
		user = self.__api.get_user(id=userID)
		if user.followers_count >= 200:
			user.follow()
			print("Your fan @" + user.screen_name + " is now being follwed!")


	def __getFansAndFollowers(self):

		# get my fans and friends
		myFollowers = self.__api.followers_ids(self.__api.me().screen_name)
		myFriends  = self.__api.friends_ids(self.__api.me().screen_name)

		return myFriends, myFollowers