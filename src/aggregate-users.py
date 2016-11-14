# Libraries
# File handling
import os, sys

# Data handling
import json, csv
from time import strftime, strptime

def commandline(arguments):
	# Function takes the commandline arguments used when calling
	# There's only one flag, a directory where the .txt file resides.
	# If the script can find it, then it'll call the aggregation function
	# If it can't then it terminates

	try:
		dataDir = arguments[1]
	except:
		return ("You need to include a directory path when calling this file.\ne.g.\tpython scriptname.py path/to/directory")

	# Best practices, check if directory exists
	if os.access(dataDir, os.F_OK):
		print (dataDir + " dir exists!")
	else:
		return ("Couldn't find your directory, sorry.")

	aggDir = createAggFolder(dataDir)

	# list all the files in a given directory
	for filename in os.listdir(dataDir):
		# only .csv files
		if filename.endswith(".txt"):

			# Agg file
			aggregateFile((dataDir + filename), aggDir)

def createAggFName(fName):
	# Function to format a new file name
	noFileExt = fName[:-4]
	aggFileName = noFileExt + '-agg.csv'
	return aggFileName

def createAggFolder(directory):
	# Function to create a new folder that's similair to the input directory
	# # 'trump-files/' -> 'trump-files-agg/'
	# so it does two in 1, makes the folder and returns the new name
	temp = directory[:-1]
	aggDirName = temp + '-agg/'

	# parent directory of direcotry from input
	parDir = os.path.abspath(os.path.join(directory, os.pardir))

	# create folder
	if not os.path.exists((parDir + aggDirName)):
		os.makedirs(aggDirName)
		print ("created {}!".format(aggDirName))

	return aggDirName

def tweetTime(created_at):
	# Helper function to take a string and return a python datetime obj
	# Example formatting from twitter: u'Fri Dec 04 00:00:32 +0000 2015'
	stamp = strptime(created_at, "%a %b %d %H:%M:%S +0000 %Y")
	return stamp

def humanTime(timestamp):
	stamp = strftime("%a %b %d %H:%M:%S +0000 %Y", timestamp)
	return stamp

def updateDict(tweet, tweets):
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
			timestamp = tweetTime(tweet['created_at'])

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
				tweets[userID]['created'] = tweetTime(user['created_at'])
	except:
		#print (tweet)
		pass

def aggregateFile(fName, aggFolder):
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
	writeOut(fName, twitterDict, corruptedLines)

	print ('\tWrittern to csv!')

def writeOut(fName, tweets, lines):
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
			tweets[key]['timestamp'] = humanTime(tweets[key]['timestamp'])
			tweets[key]['created'] = humanTime(tweets[key]['created'])
			writer.writerow(tweets[key])


if __name__ == "__main__":
	commandline(sys.argv)
