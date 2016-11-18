#! python
import os
import sys
import csv
import json
import time
import pdb
from threading import Thread, Lock, Condition
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
		#locks and condition variables for thread protection
		self.lock = Lock()
		self.cv  = Condition()
		self.keys = []
		files = []
		#Change Debug to 'True' for run time debug
		DEBUG = False
		if DEBUG:
			pdb.set_trace()

		#The unique id part of a thread id
		tid = 0
		#keeping track of each thread that is processed from the threads pool
		threadsProcessed = 0

		#The max number of threads started at one time
		MAX_ACTIVE_THREADS = 16
		#This is the thread pool
		threads = []
		#Threads limited by the number of cores
		activeThreads = []
		#time stats per thread
		self.threadDurationHistory = {}

		#The active thread count
		threadsActive = 0
		dataDir = sys.argv[1]
		if os.access(dataDir, os.F_OK):
			print (dataDir + " dir exists!")
		else:
			return ("Couldn't find your directory, sorry.")


		aggDir = self.createAggFolder(dataDir)
		# add all of the filenames to a list
		for filename in os.listdir(dataDir):
			# only .csv files
			files.append(filename)
		files = files[601:720]
	    	#enumerate over the threads
		#This is a dumb queue for now.
		#we run 24 threads, wait for them all to finish, then start 24 more
		#TODO: We could possible do this with a queue and use futures and
		#signalling to minimize waiting
		lastThread = len(files)
		filesProcessed = 0
		while (filesProcessed < len(files)):
			if ((len(files) - filesProcessed) < MAX_ACTIVE_THREADS):
				MAX_ACTIVE_THREADS = (len(files) - filesProcessed)
			while(threadsActive < MAX_ACTIVE_THREADS):
				filename = files[threadsActive]
				if filename.endswith(".txt"):
					path = (dataDir+filename)
					threadName = "Thread-"+str(threadsActive)
					print(threadName+" - filename: "+str(filename))
					thread = Thread(target = self.aggregateFile, args = (path, aggDir))
					thread.name = threadName
 					threads.append(thread)
					threads[threadsActive].start()
				   	print("Starting {}".format(threads[threadsActive].name))
				   	key = threads[threadsActive].name
				   	self.asyncWriter(key, start = 'start')
					threadsActive+=1
					filesProcessed+=1
					time.sleep(1)
			print("Active Thread Pool: {} threads are started".format(threadsActive))
			#wait for all threads to finish
			for thread in threads:

				thread.join()
				print("joined on thread {}".format(thread.name))
				#no need to worry about thread protection of timeStamps
				#we're processing joins serially.
				self.asyncWriter(thread.name)
				start = self.threadDurationHistory[thread.name][0]
				stop = self.threadDurationHistory[thread.name][1]
				threadingStats = "\n====================================================\n"
				threadingStats += "{} \t \nStart Time: {} \t Stop Time: {}".format(thread.name, start, stop)
				print(threadingStats)
			#reset the activeThreads pool and do it again

			del threads[:]
 			threadsActive = 0
			print("threads processesd {}".format(filesProcessed))

	''' func asyncWriter: lock writer so that the threadDurationHistory is protected
	'''
	def asyncWriter(self, key, start = None):
		while self.lock.locked():
			self.cv.wait()
		else:
			self.lock.acquire()
			self.cv.acquire()
			if start != None:
				self.threadDurationHistory[key] = [time.ctime(time.time())]
			else:
				self.threadDurationHistory[key].append(time.ctime(time.time()))

			self.lock.release()
			self.cv.notify_all()


	def createAggFName(self, fName):
		# Function to format a new file name
		print("fname: "+fName)
		noFileExt = fName[:-4].rsplit('/',1)[1]
		print("noFileExt: "+ noFileExt)
		aggFileName = noFileExt + '-agg.csv'
		return aggFileName

	''' func: createAggFolder()
		Creates a new folder that's similair to the input directory
	 	# 'trump-files/' -> 'trump-files-agg/'
	 	so it does two in 1, makes the folder and returns the new name
	'''
	def createAggFolder(self, directory):

		temp = directory[:-1]
		aggDirName = temp + '-agg6/'

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
			print (tweet)
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
					thread = Thread(target = self.updateDict, args =(json.loads(line), twitterDict))
					thread.start()
				except:
					corruptedLines += 1

		print ('\t{} unreadable lines\n\tWriting to dict'.format(corruptedLines))
		# WRITE IT OUT
		thread = Thread(target = self.writeOut, args =(fName, twitterDict, corruptedLines))
		thread.start()

	def writeOut(self, fName, tweets, lines):
		# Writes out a dictionairy to a csv file
		# This includes the number of corrupted lines that we're excluding

		# Get parent
		parDir = os.path.abspath(os.path.join(fName, os.pardir))
		parDirAgg = parDir + '-agg/'
		fNameAgg = self.createAggFName(fName)

		combined = parDirAgg + fNameAgg

		# column names from the twitter dictionairy
		colNames = ['userID', 'tweetsDay', 'tweetsAll', 'timestamp', 'following', 'followers', 'created', 'corrupted']

		with open(combined, 'w+b') as f:
			writer = csv.DictWriter(f, fieldnames=colNames)

			# lines
			writer.writerow({"corrupted": str(lines)})
			# header
			writer.writeheader()
			# writer.writerows(tweets)

			for key in tweets.keys():
				tweets[key]['timestamp'] = self.humanTime(tweets[key]['timestamp'])
				tweets[key]['created'] = self.humanTime(tweets[key]['created'])
				writer.writerow(tweets[key])
			print ('\tWrittern to csv!')


if __name__ == "__main__":
	if len(sys.argv) != 2:
		print "You need to include a directory path when calling this file.\ne.g.\tpython scriptname.py path/to/directory"
		exit()
	tweetParser()
