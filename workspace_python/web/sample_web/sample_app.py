
from flask import Flask, render_template, request, redirect
import pandas as pd
from sqlalchemy import create_engine


app = Flask(__name__)
engine = create_engine("oracle+cx_oracle://it:0000@localhost:1521/xe")


@app.route("/")
def hello_world():
    # return "<p>Hello, World!</p>"

    return render_template('index.html'
                           ,MY_KEY_MYLIST = 'here is nothing'
                           )


@app.route("/register_html")                       #----------------------- 웹주소
def register_html():
    return render_template('register.html')        #----------------------- .html파일


@app.route("/register")                       #----------------------- 웹주소
def register():



    with engine.connect() as conn:
        sql = """
                    create sequence users_sequence
                    start with 1 increment by 1 nocache;
                    
                    select users_sequence.nextval from dual;
                    
                    insert into users2 values(users_sequence.nextval,'lee','이씨','111','01058589696','u',null);
                    insert into users2 values(users_sequence.nextval,'kim','김씨','222','01023654787','u',1);
                    insert into users2 values(users_sequence.nextval,'park','박씨','333','01052528989','u',1);
                    insert into users2 values(users_sequence.nextval,'hong','홍씨','555','0108889999','u',3);
                    insert into users2 values(users_sequence.nextval,'admin','이관리','444','0101234567','a',null);
                    
                    commit:
            """
        df = pd.read_sql(sql, conn, params={'uid': uid})
    print(df.head())

    return render_template('')        #----------------------- .html파일



@app.route("/login_html")
def login_html():
    return render_template('login.html')


@app.route("/login", methods=['post'])
def login():

    uid = request.form.get("uid")
    upw = request.form.get("upw")
    print(uid, upw)

    # 1. SQL: 일단 아이디로 사람을 찾습니다.

    with engine.connect() as conn :
        sql = """
                    SELECT USER_ID, USER_NAME, USER_GUBUN, USER_PW 
                    FROM users 
                    where USER_UID = :uid
              """
        df = pd.read_sql(sql, conn, params={'uid': uid})
    print(df.head())


    # 2. Python: 검증 로직 수행
    if df.empty:
        return "아이디가 존재하지 않습니다."
    # DB에 있는 진짜 비밀번호 (나중엔 이게 암호화된 문자열이 됩니다)
    db_password = df.iloc[0]['user_pw']

    # 3. 비밀번호 비교 (단순 문자열 비교)
    # 나중에 암호화를 적용하면 이 부분만 check_password_hash()로 바꾸면 됩니다.
    if str(db_password) == str(upw):
        session['user_id'] = uid
        return redirect('/main')
    else:
        return "비밀번호가 틀렸습니다."

    match_user = df[(df['user_id'] == uid) & (df['user_pw'] == str(upw))]
    if not match_user.empty:
        return redirect('/rest_get')  # 성공!
    else:
        return redirect('/')  # 실패! (아이디가 없거나, 비번이 틀림)




    return render_template('/login.html',
                           KEY_uid=uid,
                           KEY_upw=upw)


@app.route("/chart_html")
def chart_html():
    return render_template('charts.html')

@app.route("/table_html")
def table_html():
    return render_template('tables.html')

@app.route("/rest_get", methods=['GET'])
def rest_get():
    # res = {"res":"get-ok"}
    # return res
    return render_template('rest_test_result.html')



@app.route("/rest_search_ajax", methods=['POST'])
def rest_search_ajax():
    # 2. AJAX 요청을 처리하는 라우트 (POST) -> 이름 바꿈
    # AJAX가 보낸 데이터 받기 (request.form 똑같이 씁니다)
    deptno = request.form.get("deptno")

    # DB 조회 로직
    with engine.connect() as conn:
        sql = """
            SELECT EMPNO, ENAME, DEPTNO
            FROM emp 
            WHERE deptno = :deptno
        """
        # params에 딕셔너리로 안전하게 전달
        df = pd.read_sql(sql, conn, params={'deptno': deptno})

    # 결과 처리
    if df.empty:
        return "<h3 style='color:red;'>검색 결과가 없습니다. 😭</h3>"

    # ★ 핵심: 전체 템플릿이 아니라, 표(Table) HTML 문자열만 딱 리턴함!
    table_html = df.to_html(classes='table table-striped table-hover table-sm w-auto',
                            header="true",
                            index=False,
                            justify='center')

    return table_html


@app.route("/form_search", methods=['post'])
def form_search():
    deptno = request.form.get("deptno")
    if not deptno:
        return render_template('rest_test.html',
                               my_table="<h3>검색어를 입력해주세요! 😅</h3>")
    with engine.connect() as conn:
        sql = """
                    SELECT EMPNO, ENAME, deptno
                    FROM emp 
                    where deptno = :deptno
                    
              """
        df = pd.read_sql(sql, conn, params={'deptno': int(deptno)})

        pass

    if df.empty:
        msg = "<h3>검색 결과가 없습니다.</h3>"
        return render_template('rest_test.html', my_table=msg)

    table_html_string = df.to_html(classes='table table-hover', header="true", index=False)

    return render_template('rest_test.html',
                           my_table=table_html_string)




@app.route("/rest_post", methods=["POST"])
def rest_post():
    uid = request.form.get("uid")
    upw = request.form.get("upw")
    habit = request.form.getlist("habit")
    gen = request.form.get("gen")
    sec = request.form.get("sec")
    addr = request.form.get("addr")
    memo = request.form.get("memo")

    print(uid, upw, habit, gen, sec, addr, memo)

    # ---------- 들어온 데이터 처리부 ---------------
    # res = {"res": "post-ok"}
    # return res
    return render_template('rest_test_result.html',
                           KEY_MY_NAME=uid)

@app.route("/rest_test_html")
def rest_test_html():
    return render_template('rest_test.html')


engine.dispose()
app.run(host='127.0.0.1', port=7777, debug=True)