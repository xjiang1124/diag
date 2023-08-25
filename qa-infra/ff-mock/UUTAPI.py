#!/usr/bin/python3

import sys
from flask import Flask
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
import json


app = Flask(__name__)
api = Api(app)


UUT_put_args = reqparse.RequestParser()

UUT_put_args.add_argument("XML Result", type=str, help="No XML Result value", required=True)

outputFile = "database.db"
file = open(outputFile, "r")
UUTs = json.load(file)

print(UUTs)

class UUT(Resource):

    def get(self, UUT_Serial, UUT_testStation):
        if UUT_Serial not in UUTs:
            abort(404, message = "Could not find UUT with that Serial Number")
        if UUT_testStation not in UUTs[UUT_Serial]:
            abort(404, message = "Found UUT, but could not find test station, try one of these keys: " + str(UUTs[UUT_Serial].keys()))
        return UUTs[UUT_Serial][UUT_testStation], 201

    def put(self, UUT_Serial, UUT_testStation):
        args = UUT_put_args.parse_args()
        #print(UUT_Serial)
        if UUT_Serial not in UUTs:
            UUTs[UUT_Serial] = dict()
        UUTs[UUT_Serial][UUT_testStation] = args
        f = open(outputFile, "w")
        f.write(json.dumps(UUTs, skipkeys=True, allow_nan=True, indent=6))
        f.close()
        return UUTs[UUT_Serial][UUT_testStation], 201

api.add_resource(UUT, "/UUT/<string:UUT_Serial>/<string:UUT_testStation>")


if __name__ == "__main__":
    app.run(host=sys.argv[1], port=5000)

