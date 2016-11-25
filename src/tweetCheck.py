#! /usr/bin/python
import os
import csv
import time
import json
import tweepy
import pandas
import logging
import botornot
from threading import Thread, Condition, Lock


class tweetCheck:
    def __init__(self):
        self.userIds = []
        logging.basicConfig(filename='output.log', level = logging.INFO)
        self.filePath = os.path.abspath(__file__).split('tweetCheck.py')[0]
    #read in userNames
        self.userIdRange = []
        self.botOrNotResults = []
        self.cv = Condition()
        self.lock = Lock()
        self.getUserIds()
        self.checkBotOrNot()

    def getUserIds(self):
        filename = 'filtered-users.csv'
        path = os.path.join(self.filePath,filename)
        csvdata = pandas.read_csv(path)
        for users in csvdata.values:
            self.userIds.append(users[0])
        i = 0
        while(i < len(self.userIds)):
            if ((len(self.userIds) -  i) < 180):
                start = i
                end = len(self.userIds) - i
                self.userIdRange.append([start, end])
            else:
                self.userIdRange.append([i, i+180])
            i+=180

    def checkBotOrNot(self):
        tokens = []
        rations = []
        screennames = []
        threads = []
        path = os.path.join(self.filePath, 'tokens.json')
        with open(path, 'r') as f:
            tokens = json.load(f)
        tokenCounter = 0
        idBin = 0
        while (idBin < len(self.userIdRange)):
            while tokenCounter < len(tokens['tokens']):
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
                    start = self.userIdRange[idBin][0]
                    end = self.userIdRange[idBin][1]

                    userIdsParam = self.userIds[start:end]

                    # auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
                    # auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
                    # api = tweepy.API(auth)

                    #save off all of the threads to start later
                    thread = Thread(target = self.botOrNot, args = (userIdsParam, twitter_app_auth))

                    threads.append(thread)

                    tokenCounter+=1
                    idBin+=1
                    if idBin >= len(self.userIdRange):
                        break
            #
            #
                except Exception as e:
                    logging.info(e)
                    tokenCounter+=1
                    idBin+=1
                    if idBin >= len(self.userIdRange):
                        break
                #start all of the threads
            for thread in threads:
                thread.start()
                logging.info("*******Thread: started thread "+thread.name+"*******")


                #join all of the threads and restart the token counter
            for thread in threads:
                thread.join()
                logging.info("*******Thread: joining on thread "+thread.name+"*******")
            tokenCounter=0
            threads[:] = []
    def botOrNot(self, userIds, auth):
        bon = botornot.BotOrNot(**auth)
        results = []
        try:
            results = list(bon.check_accounts_in(userIds))
        except Exception as e:
            logging.info(e)
        self.asyncWriter(results)

    def asyncWriter(self, results):
        try:
            self.cv.acquire()
            for result in results:
                userId =  str(result[0])
                result = result[1]
                entry = {}
                entry['userId'] = userId
                entry['result'] = result
                botOrNotData = {}
                path = os.path.join(self.filePath, 'botOrNotResults.json')
                with open(path) as f:
                    try:
                        botOrNotData = json.load(f)
                    except Exception as e:
                        logging.info(e)
                    f.close()
                try:
                    botOrNotData['botOrNot'].append(entry)
                    with open(path, 'w') as f:
                        try:
                            json.dump(botOrNotData, f, indent = 4, separators = (',',': '), sort_keys = True)
                            f.close()
                        except Exception as e:
                            f.close()
                            logging.info(e)
                except Exception as e:
                    logging.info(e)
            #Enter the critical section
            self.botOrNotResults.append(results)
            #exit critical section
            self.cv.notify_all()
            self.cv.release()
        except Exception as e:
            self.cv.wait()



def main():
    tweetCheck()


if __name__ == "__main__":
    main()
