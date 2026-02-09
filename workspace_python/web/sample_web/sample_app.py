
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


@app.route("/register_html")                       #----------------------- 웹주소
def register_html():
    return render_template('register.html')        #----------------------- .html파일

@app.route("/login_html")
def login_html():
    return render_template('login.html')

@app.route("/chart_html")
def chart_html():
    return render_template('charts.html')

@app.route("/table_html")
def table_html():
    return render_template('tables.html')


app.run(host='127.0.0.1', port=7777, debug=True)