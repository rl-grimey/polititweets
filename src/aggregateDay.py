# This script takes a single (hard coded, it's not done yet) .txt file and spits
# out a .csv of users, with a tally of how many times they tweeted that day
# along with other metrics.
#
# I plan on writing the toCSV function, along with another logic loop to
# run the script over every .txt file in a directory.

# Libraries
import json
from time import strftime, strptime

# data dir stuff....
# Eventually, this will have loop comprehension for every file within a directory
fClinton = '../data/external/clinton/hillaryclinton_1477094400.txt'
fTrump = '../data/external/trump/donaldtrump_1477699200.txt'

# Define a global twitter dictionairy
twitterDict = {}


def tweetTime(created_at):
    # Helper function to take a string and return a python datetime obj
    # Example formatting from twitter: u'Fri Dec 04 00:00:32 +0000 2015'
    stamp = strptime(created_at, "%a %b %d %H:%M:%S +0000 %Y")
    return stamp

def updateDict(tweet):
    # Function to take a tweet, and conditionally update the dictionairy
    # It takes a json input, and first checks if it's a API rate limit call

    global twitterDict
    # occasionally we'll get an API call from twitter showing up, pass those
    try:
        if tweet['limit']:
            return
    except:
        pass

    try:
        # Sanity check
        if ((tweet['user']) and (tweet['user']['id_str'])):
            user = tweet['user']
            userID = tweet['user']['id_str']

            # grab timestamp, convert timestamp
            timestamp = tweetTime(tweet['created_at'])

            # dictionairy check
            # Python 3 removed has_key, use 'in' instead
            #if (twitterDict.has_key(userID):
            if (userID in twitterDict):
                # Compare if this tweet is newer than existing data
                if (timestamp > twitterDict[userID]['timestamp']):

                    # Update friends, followers/ing, statuses
                    twitterDict[userID]['followers'] = user['friends_count']
                    twitterDict[userID]['followed'] = user['followers_count']
                    twitterDict[userID]['tweetsAll'] = user['statuses_count']

                    #and the timestamp!
                    twitterDict[userID]['timestamp'] = timestamp


                # either way, count the tweet
                twitterDict[userID]['tweetsDay'] = twitterDict[userID]['tweetsDay'] + 1

            # doesn't have key, instantiate!
            else:
                twitterDict[userID] = {'tweetsDay': 1, 'userID': userID}

                # Update friends, followers/ing, statuses
                twitterDict[userID]['followers'] = user['friends_count']
                twitterDict[userID]['followed'] = user['followers_count']
                twitterDict[userID]['tweetsAll'] = user['statuses_count']
                #and the timestamp!
                twitterDict[userID]['timestamp'] = timestamp
    except Exception as e:
        print (e)
        pass


def readLines(dayTweets):
    global twitterDict
    corruptedLines = 0

    with open(dayTweets) as f:
        for line in f:
            try:
                updateDict(json.loads(line))
            except:
                corruptedLines += 1

    print ("The number of unreadable tweets was: {}".format(corruptedLines))
    return twitterDict


# Example that returns an aggregated day of tweets
trumpAgg = readLines(fTrump)
