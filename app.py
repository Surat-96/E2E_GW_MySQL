from flask import Flask, render_template, url_for, redirect, request, session, flash, send_from_directory
import numpy as np
from operator import itemgetter
from matplotlib import pyplot as plt  
import os
import pandas as pd
import pickle
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import xlrd



#extension
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['xls'])

# app config
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


#GWQI model read
filename = open('GW-Predicting/postmonqipredict.pkl', 'rb')
postmonqi = pickle.load(filename)
filename.close()

filename = open('GW-Predicting/premonqipredict.pkl', 'rb')
premonqi = pickle.load(filename)
filename.close()



# mysql connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gwdet'

# Intialize MySQL
mysql = MySQL(app)


@app.route('/')
def index():
	return render_template('index.html')

@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        aname = request.form['aname']
        pssw = request.form['pssw']

        if(aname == 'ADMIN' and pssw == 'Surat'):
            return render_template('index1.html')
    return render_template('admin.html')


@app.route('/gwg')
def gwg():
	return render_template('graphhome.html')


@app.route('/gwdet', methods=['GET','POST'])
def gwdet():
    if request.method == 'POST':

        year = int(request.form['year'])
        sea = int(request.form['mon'])
        longi = float(request.form['long'])
        lati = float(request.form['lati'])
        temp = float(request.form['temp'])
        wd = float(request.form['wd'])
        ec = float(request.form['ec'])
        arse = float(request.form['as'])
        mn = float(request.form['mn'])
        fe = float(request.form['fe'])
        ca = float(request.form['ca'])
        calpre = int(request.form['calpre'])

        
        if calpre == 0:
            if sea==0:
                gwqi1=(3.45-0.08*wd+0.25*arse+159.56*mn+25.77*fe+0.03*ca)
                gwqi=round(gwqi1,2)
            elif sea==1:
                gwqi1=(3.10-0.01*wd+0.25*arse+159.34*mn+25.74*fe+0.04*ca)
                gwqi=round(gwqi1,2)
            else:
                print("You entered wrong.")

        elif calpre == 1:
            if sea==0:
                data = np.array([[sea,ec,arse,mn,fe,ca]])
                gwqi1 = premonqi.predict(data)
                gwqi = round(gwqi1[0],2)
            elif sea==1:
                data = np.array([[sea,ec,arse,mn,fe,ca]])
                gwqi1 = postmonqi.predict(data)
                gwqi = round(gwqi1[0],2)
            else:
                print("You entered wrong.")
        else:
                print("You entered wrong.")
        

        if gwqi<50:
            gwqc="Excellent"
        elif gwqi<100 and gwqi>50:
            gwqc="Good"
        elif gwqi<200 and gwqi>100:
            gwqc="Poor"
        elif gwqi<300 and gwqi>200:
            gwqc="Very-Poor"
        else:
             gwqc="Not-Sustainable"
    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO gw VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (year,sea,longi,lati,temp,wd,ec,arse,mn,fe,ca,gwqi,gwqc))
        mysql.connection.commit()

        return render_template('gwshow.html',sea=sea,longitude=longi,latitude=lati,temp=temp,gwqi=gwqi,gwqc=gwqc)
    return render_template('gwdet.html')   



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        full_name = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(full_name)

        sheetname = request.form['sheet']

        # Open the workbook and define the worksheet        
        book = xlrd.open_workbook(full_name)
        sheet = book.sheet_by_name(sheetname)

        # Establish a MySQL connection
        database = MySQLdb.connect (host="localhost", user = "root", passwd = "", db = "gwdet")
        # Get the cursor, which is used to traverse the database, line by line
        cursor = database.cursor()
        # Create the INSERT INTO sql query
        query = """INSERT INTO premon (id, Year, Season, Longitude, Latitude, Temp, WD, EC, ARSE, MN, FE, CA, GWQI, GWQC) 
            VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        # Create a For loop to iterate through each row in the XLS file, starting at row 2 to skip the headers
        for r in range(1, sheet.nrows):
            #id= sheet.cell(r,).value
            Year= sheet.cell(r,1).value
            Season= sheet.cell(r,2).value
            Longitude= sheet.cell(r,3).value
            Latitude= sheet.cell(r,4).value
            Temp= sheet.cell(r,5).value
            WD= sheet.cell(r,6).value
            EC= sheet.cell(r,7).value
            ARSE= sheet.cell(r,8).value
            MN= sheet.cell(r,9).value
            FE= sheet.cell(r,10).value
            CA= sheet.cell(r,11).value
            GWQI= sheet.cell(r,12).value
            GWQC= sheet.cell(r,13).value

            # Assign values from each row
            values = (Year, Season, Longitude, Latitude, Temp, WD, EC, ARSE, MN, FE, CA, GWQI, GWQC)
            #Execute sql Query
            cursor.execute(query, values)

        # Close the cursor
        cursor.close()
        # Commit the transaction
        database.commit()
        # Close the database connection
        database.close()
        
        # Print results
        print ("\nAll Done\n")
        columns = str(sheet.ncols)
        rows = str(sheet.nrows)
        print ("I just imported "+columns+" columns and "+rows+" rows to MySQL!")

        # data = pd.read_excel(file)
        return render_template('home.html')
    return render_template('gwdet.html')



# @app.route('/upload1', methods=['GET', 'POST'])
# def upload1():
#     if request.method == 'POST':
#         file = request.files['file']
#         full_name = os.path.join(UPLOAD_FOLDER, file.filename)
#         file.save(full_name)

#         sheetname = request.form['sheet']

#         # Open the workbook and define the worksheet        
#         book = xlrd.open_workbook(full_name)
#         sheet = book.sheet_by_name(sheetname)

#         # Establish a MySQL connection
#         database = MySQLdb.connect (host="localhost", user = "root", passwd = "", db = "gwdet")
#         # Get the cursor, which is used to traverse the database, line by line
#         cursor = database.cursor()
#         # Create the INSERT INTO sql query
#         query = """INSERT INTO premonsoonall (id, SamplingPeriod, Year, Season, ProjectCode, NestCode, WellCode, DepthandColor, Color, Lat, Lon, Temp, WD, EC, PH, Ars, Mn, Fe, Cl, So4, Na, Ca, Mg, K, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, GWQI, GWQC) 
#             VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

#         # Create a For loop to iterate through each row in the XLS file, starting at row 2 to skip the headers
#         for r in range(1, sheet.nrows):
#             #id= sheet.cell(r,).value
#             SamplingPeriod = sheet.cell(r,1).value
#             Year = sheet.cell(r,2).value
#             Season = sheet.cell(r,3).value
#             ProjectCode = sheet.cell(r,4).value
#             NestCode = sheet.cell(r,5).value
#             WellCode = sheet.cell(r,6).value
#             DepthandColor = sheet.cell(r,7).value
#             Color = sheet.cell(r,8).value
#             Lat = sheet.cell(r,9).value
#             Lon = sheet.cell(r,10).value
#             Temp= sheet.cell(r,11).value
#             WD= sheet.cell(r,12).value
#             EC= sheet.cell(r,13).value
#             PH = sheet.cell(r,14).value
#             Ars = sheet.cell(r,15).value
#             Mn = sheet.cell(r,16).value
#             Fe = sheet.cell(r,17).value
#             Cl = sheet.cell(r,18).value
#             So4 = sheet.cell(r,19).value
#             Na = sheet.cell(r,20).value
#             Ca = sheet.cell(r,21).value
#             Mg = sheet.cell(r,22).value
#             K = sheet.cell(r,23).value
#             Q1 = sheet.cell(r,24).value
#             Q2 = sheet.cell(r,25).value
#             Q3 = sheet.cell(r,26).value
#             Q4 = sheet.cell(r,27).value
#             Q5 = sheet.cell(r,28).value
#             Q6 = sheet.cell(r,29).value
#             Q7 = sheet.cell(r,30).value
#             Q8 = sheet.cell(r,31).value
#             Q9 = sheet.cell(r,32).value
#             Q10 = sheet.cell(r,33).value
#             Q11 = sheet.cell(r,34).value
#             GWQI= sheet.cell(r,35).value
#             GWQC= sheet.cell(r,36).value

#             # Assign values from each row
#             values = (SamplingPeriod, Year, Season, ProjectCode, NestCode, WellCode, DepthandColor, Color, Lat, Lon, Temp, WD, EC, PH, Ars, Mn, Fe, Cl, So4, Na, Ca, Mg, K, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, GWQI, GWQC)
#             #Execute sql Query
#             cursor.execute(query, values)

#         # Close the cursor
#         cursor.close()
#         # Commit the transaction
#         database.commit()
#         # Close the database connection
#         database.close()
        
#         # Print results
#         print ("\nAll Done\n")
#         columns = str(sheet.ncols)
#         rows = str(sheet.nrows)
#         print ("I just imported "+columns+" columns and "+rows+" rows to MySQL!")

#         # data = pd.read_excel(file)
#         return render_template('home.html')
#     return render_template('gwdet.html')


@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


#ADMIN PART
@app.route('/index1')
def index1():
	return render_template('index1.html')

@app.route('/postmon', methods=['GET','POST'])
def postmon():
    if request.method == 'POST':
        li=[]
    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM postmonsoonall')
        gw = cursor.fetchall()
        for i in range(len(gw)):
            li.append(gw[i])
        lt = len(li)
        #print(li)

        return render_template('manage1.html',list=li,len=lt)
    return render_template('index1.html')

@app.route('/premon', methods=['GET','POST'])
def premon():
    if request.method == 'POST':
        li=[]
    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM premonsoonall')
        gw = cursor.fetchall()
        for i in range(len(gw)):
            li.append(gw[i])
        lt = len(li)
        #print(li)

        return render_template('manage2.html',list=li,len=lt)
    return render_template('index1.html')

@app.route('/gw', methods=['GET','POST'])
def gw():
    if request.method == 'POST':
        li=[]
    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM gw')
        gw = cursor.fetchall()
        for i in range(len(gw)):
            li.append(gw[i])
        lt = len(li)
        #print(li)

        return render_template('manage3.html',list=li,len=lt)
    return render_template('index1.html')


@app.route('/bar1', methods=['GET','POST'])
def bar1():

        li=[]
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM gw')
        gw = cursor.fetchall()
        for i in range(len(gw)):
            li.append(gw[i])
        #lt = len(li)
        #print(li[1])
        ars=[]
        for i in gw:
            ars.append(i[8])
        mn=[]
        for i in gw:
            mn.append(i[9])
        yer=[]
        for i in gw:
            yer.append(i[1])

        #print(mn,'\n',yer)

        return render_template('graph0.html')#,list=li,ars=ars,fe=fe,ca=ca,mn=mn,yer=yer)

@app.route('/bar2', methods=['GET','POST'])
def bar2():
        li=[]
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM gw')
        gw = cursor.fetchall()
        for i in range(len(gw)):
            li.append(gw[i])
        #lt = len(li)
        #print(li[1])
        fe=[]
        for i in gw:
            fe.append(i[10])
        ca=[]
        for i in gw:
            ca.append(i[11])
        yer=[]
        for i in gw:
            yer.append(i[1])

        #print(mn,'\n',yer)

        return render_template('graph1.html')#,list=li,ars=ars,fe=fe,ca=ca,mn=mn,yer=yer)


        
if __name__ == '__main__':
	app.run(debug=True)





# @app.route('/gwdet', methods=['GET','POST'])
# def gwdet():
#     if request.method == 'POST':

#         sec=300;sph=8.5;smn=0.05;sfe=5;sdoc=5;snh4n=0.2;spo4p=0.05;sfl=1.5;shco3=400;sno3=10;sna=60;sca=120;smg=30;sk=5.2

#         sec1=1/sec; sph1=1/sph; smn1=1/smn; sfe1=1/sfe; sdoc1=1/sdoc; snh4n1=1/snh4n; spo4p1=1/spo4p; sfl1=1/sfl; 
#         shco31=1/shco3; sno31=1/sno3; sna1=1/sna; sca1=1/sca; smg1=1/smg; sk1=1/sk; 

#         stot=sec1+sph1+smn1+sfe1+sdoc1+snh4n1+spo4p1+sfl1+shco31+sno31+sna1+sca1+smg1+sk1

#         p=1/stot

#         wsec=p/sec; wsph=p/sph; wsmn=p/smn; wsfe=p/sfe; wsdoc=p/sdoc; wsnh4n=p/snh4n; wspo4p=p/spo4p; 
#         wsfl=p/sfl; wshco3=p/shco3; wsno3=p/sno3; wsna=p/sna; wsca=p/sca; wsmg=p/smg; wsk=p/sk; 

#         wtot=wsec+wsph+wsmn+wsfe+wsdoc+wsnh4n+wspo4p+wsfl+wshco3+wsno3+wsna+wsca+wsmg+wsk; 

#         mon = int(request.form['mon'])
#         longi = float(request.form['long'])
#         lati = float(request.form['lati'])
#         temp = float(request.form['temp'])
#         ec = int(request.form['ec'])
#         ph = float(request.form['ph'])
#         mn = float(request.form['mn'])
#         fe = float(request.form['fe'])
#         doc = float(request.form['doc'])
#         nh4n = float(request.form['nh4n'])
#         po4p = float(request.form['po4p'])
#         fl = float(request.form['fl'])
#         hco3 = float(request.form['hco3'])
#         no3 = float(request.form['no3'])
#         na = float(request.form['na'])
#         ca = float(request.form['ca'])
#         mg = float(request.form['mg'])
#         k = float(request.form['k'])

#         qec=(ec/sec); qph=((ph-7)/(sph-7)); qmn=(mn/smn); qfe=(fe/sfe); qdoc=(doc/sdoc); qnh4n=(nh4n/snh4n); qpo4p=(po4p/spo4p); 
#         qfl=(fl/sfl); qhco3=(hco3/shco3); qno3=(no3/sno3); qna=(na/sna); qca=(ca/sca); qmg=(mg/smg); qk=(k/sk); 

#         wqec=qec*wsec; wqph=qph*wsph; wqmn=qmn*wsmn; wqfe=qfe*wsfe; wqdoc=qdoc*wsdoc; wqnh4n=qnh4n*wsnh4n; wqpo4p=qpo4p*wspo4p; 
#         wqfl=qfl*wsfl; wqhco3=qhco3*wshco3; wqno3=qno3*wsno3; wqna=qna*wsna; wqca=qca*wsca; wqmg=qmg*wsmg; wqk=qk*wsk; 

#         wqtot=wqec+wqph+wqmn+wqfe+wqdoc+wqnh4n+wqpo4p+wqfl+wqhco3+wqno3+wqna+wqca+wqmg+wqk; 

#         gwqi=wqtot/wtot; 
       
#         # data = np.array([[pr,gl,bp,st,ins,bm,dp,ag]])
#         # my_prediction = model.predict(data)
#         # proba = model.predict_proba(data)[0][1]

#         # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#         # cursor.execute('INSERT INTO diabetes VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (na,pr,gl,bp,st,ins,bm,dp,ag,proba))
#         # mysql.connection.commit()
        
#         return render_template('gwshow.html')#,name=na,prediction=my_prediction,proba=proba)
#     return render_template('gwdet.html')





# plt.bar(yer, mn)
        # plt.ylim(0, 20)
        # plt.xlabel("Yer")
        # plt.ylabel("Mangnesium")
        # plt.title("Mangnesium Value Year wise")
        # plt.show()




        # names = list(map(itemgetter('Name'),li))
        # marks = list(map(itemgetter('Marks'),li))
        # print(names,'\n',marks)