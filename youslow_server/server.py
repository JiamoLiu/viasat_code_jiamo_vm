import flask
from flask import request
import pandas
import os.path
from os import path
from flask_cors import CORS
import traceback

from werkzeug.datastructures import RequestCacheControl

app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = True
app.config['CORS_HEADERS'] = 'Content-Type'
saved_filename = "video_records.csv"


@app.route('/', methods=['GET'])
def home():
    return "<h1>Youslow Server!.</p>"

@app.route('/videoparam', methods= ['POST'])
def store_video_param():
    try:
        #print(request.args.items())
        temp = dict(request.args)
        temp["loaded_fractions"] = request.get_json()["bufferFraction"]
        temp["playback_fractions"] = request.get_json()["playbackSeries"]
        df = pandas.DataFrame([temp])
        #print(df)
        if (path.exists(saved_filename)):
            df.to_csv(saved_filename,header=False, mode='a', index=False,encoding='utf-8')
        else:
            df.to_csv(saved_filename,index=False,encoding='utf-8')
        return "OK!"
    except:
        traceback.print_exc()
        return "ERROR!"


app.run(debug=True)




