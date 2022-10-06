from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from werkzeug.exceptions import NotFound

import grpc
from concurrent import futures
#import booking_pb2
#import booking_pb2_grpc
import movie_pb2
import movie_pb2_grpc

app = Flask(__name__)

PORT = 3004
HOST = '0.0.0.0'

with open('{}/data/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]


@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the User service!</h1>"


# recupérer les movies via user is et date (appelle api bookings)
@app.route("/user/booking/<userId>/<date>", methods=["GET"])
def get_user_booking_bydate(userId, date):
   r = requests.get(f"http://localhost:3003/bookings/{str(userId)}")
   if r.status_code == 400:
      return make_response({"error": "bad input parameter"}, 400)
   result = r.json()
   for dateItem in result["dates"]:
      if str(dateItem["date"]) == str(date):
         return make_response(dateItem, 200)
   return make_response({"error": "not found"}, 404)


# récupérer les movies par date via user id (appelle api bookings + movies)
@app.route("/user/booking/<userid>", methods=['GET'])
def get_movie_by_userid(userid):
   dates = requests.get('http://localhost:3003/bookings/' + userid)
   if str(dates) == '<Response [400]>':
      return make_response(jsonify({"error": "bad input parameter"}), 400)
   dates = dates.json()
   movie_tab = {'movies': []}

   with grpc.insecure_channel('localhost:3001') as channel:

      stub = movie_pb2_grpc.MovieStub(channel)

      for date in dates['dates']:
         for movie in date["movies"]:
            movieid = movie_pb2.MovieID(id=str(movie))
            res_movies = stub.GetMovieByID(movieid)
            movie_tab['movies'].append({"title":res_movies.title,"rating":res_movies.rating,"director":res_movies.director,"id":res_movies.id})

   channel.close()

   res = make_response(jsonify(movie_tab), 200)

   return res


if __name__ == "__main__":
   print("Server running in port %s" % (PORT))
   app.run(host=HOST, port=PORT)
