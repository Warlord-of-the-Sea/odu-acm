from SimpleHTTPServer import SimpleHTTPRequestHandler
import SimpleHTTPServer
import urlparse
import random
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import tweepy
from BaseHTTPServer import HTTPServer

PORT_NUMBER = 8080

#This class will handles any incoming request from
#the browser
class myHandler(SimpleHTTPRequestHandler):
    #Handler for the GET requests
    def do_GET(self):
        if self.path != "/getRaffles":
            self.path = '/public/'+ self.path
            return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET( self )

        client = MongoClient()

        db = client.raftl
        raffle_collection = db.raffles
        tweet_collection = db.tweets

        returnjson = []
        for raffle in raffle_collection.find():
            tweetjson = []
            tweets = tweet_collection.find( {'raffle_id':raffle['_id']} )
            for tweet in tweets:
                tweetjson.append( {'_id':tweet['_id'], 'user_id':tweet['user_id'], 'following':tweet['following'], 'body':tweet['body'], 'drawn':tweet.get('drawn', False),'username':tweet['username'], 'profile_img':tweet['profile_img'] })

            returnjson.append( {'id': str(raffle['_id']), 'max': raffle['max'], 'hashtag':raffle['hashtag'], 'tweets':tweetjson, 'owner':raffle.get('owner','hackuraffl') } )

        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write(json.dumps( returnjson ) )
        return

    def do_POST(self):

        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)
        params = urlparse.parse_qs( post_body )

        client = MongoClient()

        db = client.raftl
        raffle_collection = db.raffles
        tweet_collection = db.tweets

        if( self.path == '/createRaffle' ):
            raffle_collection.insert_one( {'hashtag':params['hashtag'][0], 'max':params['max'][0], 'owner':params['owner'][0] } )

            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            return

        if( self.path == '/pickWinner' ):
            raffleId = params['raffle_id'][0]

            raffle = raffle_collection.find_one( {'_id':ObjectId(raffleId) } )
            tweetcursor = tweet_collection.find( {'raffle_id':ObjectId(raffleId), 'following':True, 'drawn': {'$exists':False} } )

            tweetcount = tweetcursor.count()
            rand = random.randint( 0, tweetcount-1 )
            tweet = tweetcursor[rand]
            tweet['drawn'] = True

            auth = tweepy.OAuthHandler( '5Xr8HX71XetZYmGV86AmcEgVo', '85ql1GsrOLTRre0AqqprX9Xtm5SkMOWzJk9OVJPRiLM8bm72JA' )
            auth.set_access_token( '832250876551110658-MLGfJUjJH6Ktwlf51AQQlSO9QPcp3ew', 'UvCcyNqwH3X7u2KfRWeYvlOWxN2k1ONfjrlpxRK1Shj33' )

            api = tweepy.API( auth )

            user = api.get_user( tweet['user_id'] )
            api.update_status( '@' + user.screen_name + ' is the winner!', str(tweet['_id']) )

            tweetjson = {'_id':tweet['_id'], 'user_id':tweet['user_id'], 'following':tweet['following'], 'body':tweet['body'], 'drawn':tweet.get('drawn', False),'username':tweet['username'], 'profile_img':tweet['profile_img'] };

            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()

            self.wfile.write( json.dumps( tweetjson ) )
            tweet_collection.update_one( {'_id':tweet['_id']}, {'$set':tweet} )
            return
try:
	#Create a web server and define the handler to manage the
	#incoming request
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print 'Started httpserver on port ' , PORT_NUMBER

	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
