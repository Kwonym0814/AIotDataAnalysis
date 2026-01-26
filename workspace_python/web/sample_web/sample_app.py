
from flask import Flask, render_template
import pandas as pd


app = Flask(__name__)

@app.route("/")
def hello_world():
    # return "<p>Hello, World!</p>"
    df = pd.read_csv("../../basic/data/dept.csv")
    print(df.head())

    mylist = df['DNAME'].to_list()
    return render_template('index.html'
                           ,MY_KEY_MYLIST = mylist
                           )


app.run(host='127.0.0.1', port=7777, debug=True)