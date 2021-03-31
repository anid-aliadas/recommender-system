from flask import Flask
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)

class PredictItems(Resource):
  def get(self, user_id):
    return {'data': user_id} #Recommend(user_id, top_n)

api.add_resource(PredictItems, "/predictItems/<int:user_id>")

if __name__ == "__main__":
  app.run(debug=True)
