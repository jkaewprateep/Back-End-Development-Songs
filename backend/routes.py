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
# mongodb_service = os.environ.get('MONGODB_SERVICE')
# mongodb_username = os.environ.get('MONGODB_USERNAME')
# mongodb_password = os.environ.get('MONGODB_PASSWORD')
# mongodb_port = os.environ.get('MONGODB_PORT')

mongodb_service = "127.0.0.1";
mongodb_username = "root";
mongodb_password = "MjYxNDYtamthZXdw";
mongodb_port = "27017";

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
@app.route(("/health"), methods=['GET'])
def get_health():
    return ({"status":"OK"}, 200)

@app.route(("/count"), methods=['GET'])
def get_count():    

    result = db.songs.find({})
    result_count = len([x for x in result]);

    return ({"status": str(result_count)}, 200)

@app.route(("/song"), methods=['GET'])
def songs():    

    result = db.songs.find({});
    # result_count = len([x for x in result]);

    return ({"songs": str([x for x in result])}, 200)

@app.route(("/song/<id>"), methods=['GET'])
def get_song_by_id(id):    

    try :
        result = db.songs.find_one({"id": int(id)});

        if result :
            return (str(result), 200)
        else :
            return ({"message": "song with id not found"}, 404)
    except :
        return ({"message": "Server error"}, 500)
    
@app.route(("/song"), methods=['POST'])
def create_song(): 
    new_song = request.json;
    new_song_id = int(new_song["id"]);
    new_song_lyrics = new_song["lyrics"]
    new_song_title = new_song["title"]
    result = db.songs.find_one({"id": int(new_song_id)});

    ## If the song is existing.
    if result:
        return ({"Message": f"song with id { new_song_id } already present"}, 302)
    else :
        result = db.songs.insert_one( { "id": new_song_id, "lyrics": new_song_lyrics, "title": new_song_title } )

        result = str(result).replace("InsertOneResult", "");
        ObjectId = tuple(map(str, result.split(', ')))[0].replace("(ObjectId('", "").replace("')", "");
        Acknowledgement = tuple(map(str, result.split(', ')))[1].replace(")", "").split("=")[1];

        return ({"inserted id":{"$oid": ObjectId }}, 201)

    return ({"message": "Server error"}, 500)

@app.route(("/song/<int:id>"), methods=['PUT'])
def update_song(id): 
    new_song = request.json;
    new_song_id = int(id);
    new_song_lyrics = new_song["lyrics"]
    new_song_title = new_song["title"]

    try :
        result = db.songs.find_one({"id": new_song_id});

        if result :

            current_song_lyrics = result["lyrics"];
            current_song_title = result["title"];

            if (current_song_lyrics == new_song_lyrics) and (current_song_title == new_song_title):
                return ({"message":"song found, but nothing updated"}, 200);

            # result = db.songs.update_one( { "id": new_song_id }, 
            #                 { "lyrics" : new_song_lyrics, "title": new_song_title } )

            result = db.songs.update_one({"id": new_song_id}, 
                        {'$set': {"lyrics" : new_song_lyrics, "title": new_song_title}});
            # UpdateResult({'n': 1, 'nModified': 1, 'ok': 1.0, 'updatedExisting': True}, acknowledged=True)
            
            # if success 
            result = str(result).replace("UpdateResult", "");
            verify_result = tuple(map(str, result.split(', ')))[2];
            verify_result = int(float(verify_result.split(":")[1].strip()));

            if verify_result == 1 :
                result = db.songs.find_one({"id": new_song_id});
                new_song_Id = result["id"];
                new_song_ObjectId = result["_id"];
                new_song_lyrics = result["lyrics"];
                new_song_title = result["title"];

                return ({"_id": { "$oid": str(new_song_ObjectId) }, "id":new_song_Id, "lyrics": new_song_lyrics, "title": new_song_title}, 200)

            else :
                return ({"message": "update fail"}, 404)

        else :
            return ({"message": result}, 404)

    except Exception as err :
        return ({"message": str(err) }, 500)

@app.route(("/song/<int:id>"), methods=['DELETE'])
def delete_song(id): 

    try :
        filter = {'id': int(id) };
        result = db.songs.delete_one( filter );
        result = str(result).replace("DeleteResult", "");
        deleted_count = int(tuple(map(str, result.split(', ')))[0].split(":")[1].strip());
        # {"message":"DeleteResult({'n': 1, 'ok': 1.0}, acknowledged=True)"}

        if deleted_count <= 0 :

            return ({"message": "song not found"}, 404)
        else :

            return ({}, 204)
    except:
        return ({"message": str(err) }, 500)
    

###
# @app.route("/health")
# def healthz():
#     return jsonify(dict(status="OK")), 200

# @app.route("/count")
# def count():
#     """return length of data"""
#     count = db.songs.count_documents({})

#     return {"count": count}, 200

# @app.route("/song", methods=["GET"])
# def songs():
#     # docker run -d --name mongodb-test -e MONGO_INITDB_ROOT_USERNAME=user
#     # -e MONGO_INITDB_ROOT_PASSWORD=password -e MONGO_INITDB_DATABASE=collection mongo
#     results = list(db.songs.find({}))
#     print(results[0])
#     return {"songs": parse_json(results)}, 200

# @app.route("/song/<int:id>", methods=["GET"])
# def get_song_by_id(id):
#     song = db.songs.find_one({"id": id})
#     if not song:
#         return {"message": f"song with id {id} not found"}, 404
#     return parse_json(song), 200

# @app.route("/song", methods=["POST"])
# def create_song():
#     # get data from the json body
#     song_in = request.json

#     print(song_in["id"])

#     # if the id is already there, return 303 with the URL for the resource
#     song = db.songs.find_one({"id": song_in["id"]})
#     if song:
#         return {
#             "Message": f"song with id {song_in['id']} already present"
#         }, 302

#     insert_id: InsertOneResult = db.songs.insert_one(song_in)

#     return {"inserted id": parse_json(insert_id.inserted_id)}, 201

# @app.route("/song/<int:id>", methods=["PUT"])
# def update_song(id):

#     # get data from the json body
#     song_in = request.json

#     song = db.songs.find_one({"id": id})

#     if song == None:
#         return {"message": "song not found"}, 404

#     updated_data = {"$set": song_in}

#     result = db.songs.update_one({"id": id}, updated_data)

#     if result.modified_count == 0:
#         return {"message": "song found, but nothing updated"}, 200
#     else:
#         return parse_json(db.songs.find_one({"id": id})), 201

# @app.route("/song/<int:id>", methods=["DELETE"])
# def delete_song(id):

#     result = db.songs.delete_one({"id": id})
#     if result.deleted_count == 0:
#         return {"message": "song not found"}, 404
#     else:
#         return "", 204