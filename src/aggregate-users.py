#! python
import os
import sys
import csv
import json
from threading import Thread
from time import strftime, strptime

'''
This is a class to perform parsing operations of twitter tweets.
'''
class tweetParser:
	'''
		func: __init__()
		There's only one flag, a directory where the .txt file resides.
		If the script can find it, then it'll call the aggregation function
		If it can't then it terminates. Best practices, check if directory exists
	'''
	def __init__(self):
		files = []

		threadId = 0
		tid = 0
		threadsProcessed = 0
		MAX_ACTIVE_THREADS = 24

		threads = []
		activeThreads = []
		threadDurationHistory = []

		print sys.argv[1]
		dataDir = sys.argv[1]
		print dataDir

		if os.access(dataDir, os.F_OK):
			print (dataDir + " dir exists!")
		else:
			return ("Couldn't find your directory, sorry.")

		aggDir = self.createAggFolder(dataDir)

		# add all of the filenames to a list
		for filename in os.listdir(dataDir):
			# only .csv files
			fileList.append(filename)

		# create a thread to process each file and add it to the threads pool.
		for filname in files:
			if filename.endswith(".txt"):
				path = (dataDir + filename)
				threadName = "Thread-"+tid
				thread = Thread(target = self.aggregateFile, args = path, aggDir)
				thread.name = threadName
				threads.append(thread)
				tid+=1
		print "Added {} to threads pool".format(len(threads))

	    #enumerate over the threads
		#This is a dumb queue for now.
		#we run 24 threads, wait for them all to finish, then start 24 more
		#TODO: We could possible do this with a queue and use futures and
		#signalling to minimize waiting.
		while (threadsProcessed < len(threads)):
			timePair = []
			while (activeThreads < MAX_ACTIVE_THREADS or
				   threadsProcessed == len(threads)):
				   threads[threadsProcessed].start()
				   key = threads[threadsProcessed].name
				   timePair.append(self.timeStampNow())
				   threadDurationHistory[key] = timePair
   				   activeThreads += 1
   				   threadsProcessed += 1
				   del timePair[:]
			#wait for all threads to finish
			for thread in activeThreads:
				thread.join()
				#no need to worry about thread protection of timeStamps
				#were processing joins serially.
				threadDurationHistory[thread.name].append(self.timeStampNow())
				start = threadDurationHistory[thread.name][0]
				stop = threadDurationHistory[thread.name][1]
				print "{} \t\t Start Time: {} \t\t Stop Time {}".format(thread.name, start, stop)
			#reset the activeThreads pool and do it again
			del activeThreads[:]
			activeThreads = 0

	def timeStampNow(self):
		timestamp = time.ctime(time.time())
		return timestamp

	def createAggFName(self, fName):
		# Function to format a new file name
		noFileExt = fName[:-4]
		aggFileName = noFileExt + '-agg.csv'
		return aggFileName

	''' func: createAggFolder()
		Creates a new folder that's similair to the input directory
	 	# 'trump-files/' -> 'trump-files-agg/'
	 	so it does two in 1, makes the folder and returns the new name
	'''
	def createAggFolder(self, directory):

		temp = directory[:-1]
		aggDirName = temp + '-agg/'

		# parent directory of direcotry from input
		parDir = os.path.abspath(os.path.join(directory, os.pardir))

		# create folder
		if not os.path.exists((parDir + aggDirName)):
			os.makedirs(aggDirName)
			print ("created {}!".format(aggDirName))

		return aggDirName

	''' func: tweetTime()
		Helper function to take a string and return a python datetime obj
		Example formatting from twitter: u'Fri Dec 04 00:00:32 +0000 2015'
	'''
	def tweetTime(self, created_at):

		stamp = strptime(created_at, "%a %b %d %H:%M:%S +0000 %Y")
		return stamp

	def humanTime(self, timestamp):
		stamp = strftime("%a %b %d %H:%M:%S +0000 %Y", timestamp)
		return stamp

	def updateDict(self, tweet, tweets):
	 	# Function to take a tweet, and conditionally update the dictionairy
		# occasionally we'll get an API call from twitter showing up, pass those
		try:
			if tweet['limit']:
				return
		except:
			pass

		try:
			# Sanity check
			if ((tweet['user']) and (tweet['user']['id'])):

				user = tweet['user']
				userID = tweet['user']['id_str']

				# grab timestamp, convert timestamp
				timestamp = self.tweetTime(tweet['created_at'])

				# dictionairy check
				if userID in tweets:

					# Compare if this tweet is newer than existing data
					if (timestamp > tweets[userID]['timestamp']):

						# Update friends, followers/ing, statuses
						tweets[userID]['following'] = user['friends_count']
						tweets[userID]['followers'] = user['followers_count']
						tweets[userID]['tweetsAll'] = user['statuses_count']

						#and the timestamp!
						tweets[userID]['timestamp'] = timestamp


					# either way, count the tweet
					tweets[userID]['tweetsDay'] = tweets[userID]['tweetsDay'] + 1

				# doesn't have key, instantiate!
				else:
					tweets[userID] = {'tweetsDay': 1, 'userID': userID}

					# Update friends, followers/ing, statuses
					tweets[userID]['following'] = user['friends_count']
					tweets[userID]['followers'] = user['followers_count']
					tweets[userID]['tweetsAll'] = user['statuses_count']
					#and the timestamp of the last seen tweet!
					tweets[userID]['timestamp'] = timestamp
					# User creation time
					tweets[userID]['created'] = self.tweetTime(user['created_at'])
		except:
			#print (tweet)
			pass

	def aggregateFile(self, fName, aggFolder):
		# Function to aggregate a candidate's twitter stream .txt
		# Outputs a .csv file of the users in the file

		# feedback
		print ('{} starting...'.format(fName))
		# Dict we'll be keeping
		twitterDict = {}
		# Counter for unreadable lines.
		corruptedLines = 0

		# Now open it up
		with open(fName) as f:
			# # #
			# # # YOU COULD THREAD THIS FOR A FASTER PERFORMANCE
			# # #
			for line in f:
				try:
					updateDict(json.loads(line), twitterDict)
				except:
					corruptedLines += 1

		print ('\t{} unreadable lines\n\tWriting to dict'.format(corruptedLines))
		# WRITE IT OUT
		self.writeOut(fName, twitterDict, corruptedLines)

		print ('\tWrittern to csv!')

	def writeOut(self, fName, tweets, lines):
		# Writes out a dictionairy to a csv file
		# This includes the number of corrupted lines that we're excluding

		# Get parent
		#parDir = os.path.abspath(os.path.join(fName, os.pardir))
		#parDirAgg = parDir + '-agg'
		fNameAgg = createAggFName(fName)

		# column names from the twitter dictionairy
		colNames = ['userID', 'tweetsDay', 'tweetsAll', 'timestamp', 'following', 'followers', 'created', 'corrupted']

		with open(fNameAgg, 'wb') as f:
			writer = csv.DictWriter(f, fieldnames=colNames)

			# lines
			writer.writerow({"corrupted": str(lines)})
			# header
			writer.writeheader()
			#writer.writerows(tweets)

			for key in tweets.keys():
				tweets[key]['timestamp'] = self.humanTime(tweets[key]['timestamp'])
				tweets[key]['created'] = self.humanTime(tweets[key]['created'])
				writer.writerow(tweets[key])


if __name__ == "__main__":
	print len(sys.argv)
	if len(sys.argv) != 2:
		print "You need to include a directory path when calling this file.\ne.g.\tpython scriptname.py path/to/directory"
		exit()
	tweetParser()
