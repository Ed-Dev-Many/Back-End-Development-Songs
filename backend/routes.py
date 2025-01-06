from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

#health check get
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status":"OK"}), 200

#count
@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})

    return jsonify({"count": count}), 200


@app.route("/song", methods=["GET"])
def songs():
    try:
        # Fetch all documents from the 'songs' collection
        cursor = db.songs.find({})
        # Convert the cursor to a list of dictionaries
        # song_list = [doc for doc in cursor]
        # Return the list of songs as a JSON response
        return jsonify({"songs": json_util.dumps(cursor)}), 200
    except Exception as e:
        # Log the error and return a 500 status code with the error message
        app.logger.error(f"Error in /song endpoint: {str(e)}")
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    try:
        # Use the db.songs.find_one method to find a song by its ID
        song = db.songs.find_one({"id": id})
       
        if song:
            # Return the song as JSON with a status of HTTP 200 OK
            return jsonify(json_util.dumps(song)), 200
        else:
            # Return a message if the song with the specified ID is not found
            return jsonify({"message": "song with id not found"}), 404
    except Exception as e:
        # Log the error and return a 500 status code with the error message
        app.logger.error(f"Error in /song/<id> endpoint: {str(e)}")
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@app.route("/song", methods=["POST"])
def create_song():
    try:
        # Extract the song data from the request body
        new_song = request.json
        # Check if the request body is empty or not JSON
        if not new_song:
            return {"Message": "Invalid input parameter"}, 422        # Check if 'id' exists in the incoming song data
        if 'id' not in new_song:
            return {"Message": "Missing 'id' in input data"}, 422

        # Check if a song with the same 'id' already exists in the database
        existing_song = db.songs.find_one({"id": new_song['id']})
        if existing_song:
            return {"Message": f"song with id {new_song['id']} already present"}, 302

        result = db.songs.insert_one(new_song)
        # Return a success message with the inserted '_id' in the MongoDB ObjectId format
        return {"inserted id": {"$oid": str(result.inserted_id)}}, 201        # Return a success message with the inserted 'id' and a 201 Created status code
    except Exception as e:
        # Log the error and return a 500 status code with the error message
        app.logger.error(f"Error in /song/<id> POST endpoint: {str(e)}")
        return {"Message": "An error occurred", "error": str(e)}, 500


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    # Extract the song data from the request body
    upt_song = request.json
    # Check if a song with the same 'id' already exists in the database
    existing_song = db.songs.find_one({"id": id})
    if existing_song == None:
        return {"message": "song not found"}, 404

    updated_data = {"$set": upt_song}
    result = db.songs.update_one({"id": id}, updated_data)
    if result.modified_count == 0:
        return {"message": "song found, but nothing updated"}, 200
    else:
        return parse_json(db.songs.find_one({"id": id})), 201

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id": id})
    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    else:
        return "", 204
        app.logger.error(f"Error in /song/<id> POST endpoint: {str(e)}")
        return {"Message": "An error occurred", "error": str(e)}, 500
