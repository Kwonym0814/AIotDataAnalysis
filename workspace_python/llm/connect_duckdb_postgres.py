import duckdb

conn = duckdb.connect()
conn.execute("INSTALL postgres")
conn.execute("LOAD postgres")

conn.execute("""
    ATTACH 'dbname=newsdb user=newsuser password=news1234 host=localhost port=5432'
    AS pg (TYPE postgres)
""")

print("연결 성공")


