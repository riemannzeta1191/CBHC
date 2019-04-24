import json
import flask
from flask import Flask,Response
from flask.json import jsonify
app = Flask(__name__)
import requests
import infermedica_api
from flask import request
from flask import make_response
import redis
from typing import NamedTuple
redis = redis.StrictRedis()


# Caution: The developer access token is used for /intents and /entities endpoints.
# The client access token is used for /query, /contexts, and /userEntities endpoints.
symptom_id = "354e269b-efa9-4526-8f86-2875f40aa57b"

client_token = "4514385e5b1d49c790b78e65d2630aab"
dev_token = "41674147f6644f09a6fee7ed4bb34d3c"
v = "20150910"
import dialogflow as dialogflow

root = "https://api.dialogflow.com/v1/"
headers = {"App-Id":"a81bc24b","App-Key":"fb1906fbbbed7a700174a6bcc7eaf602","Content-Type":"application/json"}

header_0 = {"Authorization":"Bearer "}
header_1 = {"Authorization": "Bearer 41674147f6644f09a6fee7ed4bb34d3c"}
# response = requests.get("https://api.dialogflow.com/v1/query?v=20150910&sessionId=12345&lang=en&query=hi",headers=header_1)

# default route
@app.route('/')
def index():
    return 'Hello World!'

# create a route for webhook


any_more = 0


def results(res):
    global any_more
    if res.get("result").get("action")!= "get_results":
        return {}
    res_dict = {}
    result = res["result"]
    context = result["contexts"]
    query = result["resolvedQuery"]
    response = requests.post("https://api.infermedica.com/v2/parse", data=json.dumps({"text":query}),headers=headers)
    json_resp = response.json()
    print(json_resp)
    b= [[i["common_name"],i["id"]] for i in json_resp["mentions"] if i["choice_id"]=="present"]
    symptoms.extend(b)
    print(symptoms)
    return {"speech":"I got your symptoms"},{"is_symptoms":True,"age":context[0]["parameters"]["age.original"],
            "duration":context[0]["parameters"]["duration.original"],"gender":context[0]["parameters"]["gender"]}


def diagnosis(res):
    import infermedica_api
    api = infermedica_api.get_api()
    if res.get("result").get("action") != "get_results":
        return {}
    result = res["result"]
    context = result["contexts"]
    query = result["resolvedQuery"]
    infer_request = infermedica_api.Diagnosis(sex=context[0]["parameters"]["gender"], age=context[0]["parameters"]["age.original"])
    for elem in symptoms:
        infer_request.add_symptom(elem[1], 'present')
    infer_request = api.diagnosis(infer_request)
    print(infer_request.conditions)
    try:
        length = len(infer_request.__dict__["conditions"])
        s1 = infer_request.__dict__["conditions"][0]["common_name"]
        s2 = infer_request.__dict__["conditions"][1]["common_name"]
        s3 = infer_request.__dict__["conditions"][2]["common_name"]
        if length >= 3:
            return {"speech": s1 + " or " + s2 + " or " + s3 }
    except (KeyError,IndexError):
        s1 = infer_request.__dict__["conditions"][0]["common_name"]
        return {"speech": s1}




@app.route('/webhook', methods = ['POST'])
def webhook():
    req = request.get_json(force=True, silent=True)
    res,others = results(req)
    diag = diagnosis(req)
    res = json.dumps(res,indent=4)
    diag = json.dumps(diag)
    print(res)
    if others["is_symptoms"]==True:
        r = make_response(res)
        d = make_response(diag)
        r.headers['Content-Type'] = "application/json"
        d.headers['Content-Type'] = "application/json"
        return d


if __name__ == '__main__':
    import infermedica_api
    infermedica_api.configure(app_id='a81bc24b', app_key='fb1906fbbbed7a700174a6bcc7eaf602')
    symptoms = []
    app.run(debug=True,host='0.0.0.0')
