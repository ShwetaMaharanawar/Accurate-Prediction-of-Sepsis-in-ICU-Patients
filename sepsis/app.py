from flask import Flask, redirect, render_template, url_for, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pickle
import pandas as pd
import numpy as np
import joblib 
import secrets
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple


app = Flask(__name__)
app.config['SECRET_KEY'] = '\x01s\xdc<+z\xe0V\xcc\x16\xd3&\xfb\xcc\xca\xf5\x1e\x8a{PB\xdc\x9f\xc3' 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///result.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class result(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    hni_id = db.Column(db.Integer, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sofa_score = db.Column(db.Integer, nullable=False)
    qsofa_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(200), nullable=False)
    result = db.Column(db.String(200), nullable=False)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.name}"

def create_tables():
    db.create_all()
    
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/page1')
def page1():
    return render_template('page1.html')


# @app.route('/page2', methods=['GET', 'POST'])
# def page2():
#     if request.method == 'POST':
#         nhi = request.form['nhi_no']
#         name = request.form['name']
#         # Assuming you also have 'last_name' in your form
#         last_name = request.form['last_name']

#         # Now you can use these values, for example, redirect to another page
#         return redirect(url_for('page3'))

#     return render_template('page2.html')

# @app.route('/page2', methods=['GET', 'POST'])
# def page2():
#     if request.method=='POST':
#         nhi = request.form['nhi_no']
#         name = request.form['name']
#         session['nhi'] = nhi
#         session['name'] = name
#     return render_template('page2.html')


# @app.route('/page3', methods=['GET', 'POST'])
# def page3():
#     return render_template('page3.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     return render_template('login.html')

#********************
@app.route('/page2', methods=['GET', 'POST'])
def page2():
    if request.method == 'POST':
        id = request.form['nhi_no']
        name = request.form['name']+" "+request.form['last_name']
        age = request.form['age']
        return redirect(url_for('page3', id=id, name=name, age=age))
    return render_template('page2.html')

@app.route('/page3', methods=['GET', 'POST'])
def page3():
    if request.method == 'POST':
        sys_type = request.form['sys_type']
        result_ans = "High Risk"  # You may get this from your prediction logic
        result_adding = result(name=session.get('name'), nhi=session.get('nhi_no'), sys=sys_type, result=result_ans)
        db.session.add(result_adding)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('page3.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entered_password = request.form['password']

        # Replace 'your_predefined_password' with the actual predefined password
        predefined_password = '12345678'

        if entered_password == predefined_password:
            return redirect(url_for('admin'))
        else:
            error_message = 'Incorrect password. Please try again.'
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

@app.route('/predict', methods=['POST'])
def predict():
    
    
    model_path = 'model.pkl'  # Update this path
    model = joblib.load(model_path)

    features_no_sepsis_new = [
        request.form['p_id'],  # Patient_ID (unique identifier)
        request.form['heart_rate'], # Heart rate
        request.form['o2s'], # Heart rate
        request.form['temp'], # Heart rate
        request.form['map'], # Heart rate
        request.form['respiratory'], # Heart rate
        request.form['sbp'], # Heart rate
        request.form['dbp'], # Heart rate
        request.form['respiratory_sys'], # Heart rate
        request.form['kidney'], # Heart rate
        request.form['coagulation'], # Heart rate
        request.form['liver'], # Heart rate
        request.form['p_age'], # Heart rate
    ]

    # Assuming the necessary imports and model loading have been done
    feature_vector_no_sepsis_new = np.array(features_no_sepsis_new).reshape(1, -1)

    # Make a prediction using the new feature vector
    prediction_new = model.predict(feature_vector_no_sepsis_new)

    # Interpret the new prediction
    prediction_result_new = "Sepsis Detected" if prediction_new[0] == 1 else "Sepsis Not Detected"
    # print(f"New Prediction: {prediction_result_new}")
    #
    if request.form['qsofa']=='1' and prediction_result_new == "Sepsis Detected":
        level = "Low Risk"
        qsofa = request.form['qsofa']
    elif request.form['qsofa']=='2'and prediction_result_new == "Sepsis Detected":
        level = "Medium Risk"
        qsofa = request.form['qsofa']
    elif request.form['qsofa']=='3' and prediction_result_new == "Sepsis Detected":
        level = "High Risk"
        qsofa = request.form['qsofa']
    else:
        level = "None"
        qsofa = "0"

    add_result = result(name=request.form['p_name'], hni_id=request.form['p_id'], age=request.form['p_age'], sofa_score=request.form['sofa'], qsofa_score = qsofa, risk_level = level, result=prediction_result_new)
    db.session.add(add_result)
    db.session.commit()

    return jsonify({"prediction": prediction_result_new, "level":level})


@app.route('/admin')
def admin():
    allresult = result.query.all()
    return render_template('admin.html', allresult=allresult)

#******************
# @app.route('/admin')
# def admin():
#     nhi = session.get('nhi')
#     name = session.get('name')
#     result_adding = result(name=name, nhi=nhi, sys="respitory", result="High Risk")
#     db.session.add(result_adding)
#     db.session.commit()
#     allresult = result.query.all() 
#     return render_template('admin.html', allresult=allresult)

# @app.route('/admin')
# def admin():
#     result_adding = result(name="dummy_name", nhi="7854", sys="respitory", result_ans="High Risk")
#     db.session.add(result)
#     db.session.commit()
#     # print(result_adding)
#     allresult = result.query.all() 
#     return render_template('admin.html', allresult = allresult )





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)