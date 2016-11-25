#! /usr/bin/python
import os
import csv
import time
import json
import tweepy
import pandas
import botornot
from threading import Thread, Condition, Lock


class tweetCheck:
    def __init__(self):
        self.userIds = []
    #read in userNames
        self.userIdRange = []
        self.botOrNotResults = []
        self.cv = Condition()
        self.lock = Lock()
        self.getUserIds()
        self.checkBotOrNot()

    def getUserIds(self):
        csvdata = pandas.read_csv('filtered-users.csv')
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
        with open('tokens.json', 'r') as f:
            tokens = json.load(f)
        tokenCounter = 0
        idBin = 0
        while (idBin < len(self.userIdRange)):
            while tokenCounter < len(tokens['tokens']):
                try:
                    print '**********'+str(tokenCounter)+'******************'
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
                    print e
                    tokenCounter+=1
                    idBin+=1
                    if idBin >= len(self.userIdRange):
                        break
                #start all of the threads
            for thread in threads:
                thread.start()
                print "*******Thread: started thread "+thread.name+"*******"


                #join all of the threads and restart the token counter
            for thread in threads:
                thread.join()
                print "*******Thread: joining on thread "+thread.name+"*******"
            tokenCounter=0
            threads[:] = []
    def botOrNot(self, userIds, auth):
        bon = botornot.BotOrNot(**auth)
        results = []
        try:
            results = list(bon.check_accounts_in(userIds))
        except Exception as e:
            print e
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
                with open('botOrNotResults.json') as f:
                    try:
                        botOrNotData = json.load(f)
                    except Exception as e:
                        print e
                    f.close()
                try:
                    botOrNotData['botOrNot'].append(entry)
                    with open('botOrNotResults.json', 'w') as f:
                        try:
                            json.dump(botOrNotData, f, indent = 4, separators = (',',': '), sort_keys = True)
                            f.close()
                        except Exception as e:
                            f.close()
                            print e
                except Exception as e:
                    print e
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
