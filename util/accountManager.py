import os
import tweepy
from random import randint
import pandas as pd

FOLLOWER_LOG_PATH = os.getcwd() + "/log/"
FOLLOWR_LOG_FILE = "followerLog.csv"



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


	def unfollowTraitors(self):
		
		# read old follower file remove old
		# followers list (if not present then create one)
		followerFile = FOLLOWER_LOG_PATH + FOLLOWR_LOG_FILE
		oldFollowers = pd.DataFrame()

		if os.path.lexists(followerFile):
			oldFollowers = pd.read_csv(followerFile)
			os.remove(followerFile)
		else:
			# This is the first time !
			self.createFollowersFile()
			return

		# retrive list of current followers and
		_, myFollowers = self.__getFansAndFollowers()

		# find traitors and unfollow them!!
		olds = list(oldFollowers["ID"])
		self.__unfollowTraitors(olds,myFollowers)

		# save the current follower file. Update myFollowers
		# since someone may have followed you in when running the
		# code!!
		self.createFollowersFile()		


	def createFollowersFile(self):

		followerFile = FOLLOWER_LOG_PATH + FOLLOWR_LOG_FILE
		# create a file of current followers
		_, myFollowers = self.__getFansAndFollowers()

		# create dataframe to save the followers
		followers = pd.DataFrame(myFollowers,columns=["ID"])
		# self.__getFollowerMetaData(followers)
		# save it
		followers.to_csv(followerFile,sep=",")



	def __unfollowTraitors(self,olds,myFollowers):
		
		# Release the Krakon!!
		for oldF in olds:
			if oldF not in myFollowers:
				traitor = self.__api.get_user(id=oldF)
				traitor.unfollow()
				print("User @" + traitor.screen_name +\
					" was unfollowed!")



	def __getFollowerMetaData(self,followers):
		print(followers)
		
		# get user screen name
		followers["screen name"] = followers.apply\
		(lambda x:self.__api.get_user(id=x["ID"]).screen_name,axis=1)

		# get number of followers
		followers["followers count"] = followers.apply\
		(lambda x:self.__api.get_user(id=x["ID"]).followers_count,axis=1)		
