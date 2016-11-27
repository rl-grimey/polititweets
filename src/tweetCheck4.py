#! /usr/bin/python
import os
import csv
import time
import json
import Queue
import tweepy
import pandas
import logging
import botornot
from threading import Thread, Condition, Lock


class tweetCheck:
    def __init__(self):
        self.userIds = []
        logging.basicConfig(filename='output4.log', level = logging.INFO)
        self.filePath = os.path.abspath(__file__).split('tweetCheck4.py')[0]
        #read in userNames
        self.botOrNotResults = []
        self.cv = Condition()
        self.bonCv = Condition()
        self.getUserIds()
        self.checkBotOrNot()

    def getUserIds(self):
        logging.info("getUserIds")

        filename = 'filtered-users.csv'
        path = os.path.join(self.filePath,filename)
        csvdata = pandas.read_csv(path)
        for users in csvdata.values:
            self.userIds.append(users[0])
        self.userIds = self.userIds[42461:56614]


    def checkBotOrNot(self):
        logging.info("checkBotOrNot")
        tokens = []
        rations = []
        screennames = []
        threads = []
        path = os.path.join(self.filePath, 'tokens4.json')
        with open(path, 'r') as f:
            tokens = json.load(f)
        tokenCounter = 0
        userid = 0
        while (userid < len(self.userIds)):
            while ((tokenCounter < len(tokens['tokens']))):

                try:
                    logging.info('**** Token: '+str(tokenCounter)+'****')
                    CONSUMER_KEY = tokens['tokens'][tokenCounter]['consumerKey']
                    CONSUMER_SECRET = tokens['tokens'][tokenCounter]['consumerSecret']
                    ACCESS_TOKEN = tokens['tokens'][tokenCounter]['accessToken']
                    ACCESS_TOKEN_SECRET = tokens['tokens'][tokenCounter]['accessTokenSecret']

                    twitter_app_auth = {
                            'consumer_key': CONSUMER_KEY,
                            'consumer_secret': CONSUMER_SECRET,
                            'access_token': ACCESS_TOKEN,
                            'access_token_secret': ACCESS_TOKEN_SECRET
                    }

                    userIdsParam = self.userIds[userid]

                    # auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
                    # auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
                    # api = tweepy.API(auth)

                    #save off all of the threads to start later
                    thread = Thread(target = self.botOrNot, args = (userIdsParam, twitter_app_auth))
                    threads.append(thread)
                    tokenCounter+=1
                    userid+=1

            #
            #
                except Exception as e:
                    logging.info(e)
                    tokenCounter+=1
                    userid+=1

            #start all of the threads
            for thread in threads:
                thread.start()
                logging.info("*******Thread: started thread "+thread.name+"*******")


            #join all of the threads and restart the token counter
            for thread in threads:
                thread.join(timeout = 15.0)
                logging.info("*******Thread: joining on thread "+thread.name+"*******")
            tokenCounter=0
            threads[:] = []
            self.asyncWriter(self.botOrNotResults)
            logging.info("*** procecesed bon logs")
            self.botOrNotResults[:] = []

    def botOrNot(self, userIds, auth):
        results = None
        while results == None:

            try:
                self.bonCv.acquire()
                bon = botornot.BotOrNot(**auth)
                results = bon.check_account(userIds)
                logging.info("results")
                logging.info(results)
                self.botOrNotResults.append(results)
                logging.info("**** TOTAL USERS: "+str(len(self.botOrNotResults)))
                self.bonCv.notify_all()
                self.bonCv.release()

            except:
                self.bonCv.wait(timeout = 1.0)

    def asyncWriter(self, resultsList):
        try:
            for results in resultsList:
                print "results"
                print results
                userId =  results['meta']['user_id']
                screenName = results['meta']['screen_name']
                entry = {}
                entry['user_id'] = userId
                entry['screen_name'] = screenName
                entry['score'] = results['score']
                entry['categories'] = results['categories']
                botOrNotData = {}
                path = os.path.join(self.filePath, 'botOrNotResults4.json')
                with open(path) as f:
                    try:
                        botOrNotData = json.load(f)
                    except Exception as e:
                        print e
                        logging.info(e)
                    f.close()
                try:
                    botOrNotData['botOrNot'].append(entry)
                    with open(path, 'w') as f:
                        try:
                            json.dump(botOrNotData, f, indent = 4, separators = (',',': '), sort_keys = True)
                            f.close()
                        except Exception as e:
                            print e
                            f.close()
                            logging.info(e)
                except Exception as e:
                    print e
                    logging.info(e)
        except Exception as e:
            print e
            logging.info(e)


def main():
    tweetCheck()


if __name__ == "__main__":
    main()
