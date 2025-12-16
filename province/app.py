from flask import Flask, render_template, request,jsonify
import pymysql

app = Flask(__name__)

conn =  pymysql.connect(
    host = 'localhost',
    user= 'root',
    password='huaji233',
    database='china_region',
    charset='utf8mb4',
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/getProvinces')
def get_provinces():
    with conn.cursor() as cursor:
        sql = "SELECT province,name FROM province WHERE city ='0' AND area='0' AND town ='0'"
        cursor.execute(sql)
        rows = cursor.fetchall()
        result=[{'code':r[0],'name':r[1]} for r in rows]
    return jsonify(result)
    
@app.route('/getCities')
def get_cities():
    province_code = request.args.get('province')
    with conn.cursor() as cursor:
        sql = """
                SELECT code,name FROM province
                WHERE province=%s AND city!='0' AND area='0' and town='0'
            """
        cursor.execute(sql,(province_code,))
        rows = cursor.fetchall()
        result=[{'code':r[0],'name':r[1]} for r in rows]
    return jsonify(result)

@app.route('/getAreas')
def get_areas():
    province_code = request.args.get('province')
    with conn.cursor() as cursor:
        sql="""
            SELECT code,name FROM province 
            WHERE province=%s AND area!='0' AND town='0'
            """
        cursor.execute(sql,(province_code,))
        rows = cursor.fetchall()
        result = [{'code':r[0],'name':r[1]}for r in rows]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)