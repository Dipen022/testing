

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
import pandas as pd
import statistics
import math
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from io import BytesIO
import base64


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret_key'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            flash('Login successful', 'success')
            return redirect(url_for('data_analysis'))
        else:
            flash('Login failed. Check your username and password.', 'danger')

            

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')



#@app.route('/perform_surfactant_analysis', methods=['GET', 'POST'])
def perform_surfactant_analysis(sample1, sample2):
    # read the entire data feed csv file of Thingspeak into data frame
    # data = pd.read_csv("C:\\Users\\Admin\\Downloads\\DummyDataSet.csv")
    data = pd.read_csv("FinalDataSet.csv")

    # create empty dataframe to save the processed data
    df = pd.DataFrame(columns=['Sample', 'Conc', 'Conductivity', 'ConRoot', 'Molar'])

    # finding unique values of sample IDs in the data set
    SampleList = data.Sample.unique().tolist()

    for item in SampleList:
        FilteredDataSample = data[(data.Sample == item)]

        ConcList = FilteredDataSample.Concentration.unique().tolist()
        for concentration in ConcList:
            FilteredConcentration = FilteredDataSample[(FilteredDataSample.Concentration == concentration)]
            mean_conductivity = round(statistics.mean(FilteredConcentration['Conductivity']), 2)
            conroot = round(math.sqrt(concentration), 2)

            if concentration == 0:
                molar_conductance = float('inf')
            else:
                molar_conductance = round(((1000 * mean_conductivity) / concentration), 2)

            addlist = [item, concentration, mean_conductivity, conroot, molar_conductance]
            df.loc[len(df)] = addlist

    # filtering out specific sample related dataframe
    filtered_df = df[(df['Sample'] == sample1) | (df['Sample'] == sample2)].copy()
    filtered_df = filtered_df.reset_index(drop=True)
    # calculation of slope
    DataLength = len(filtered_df['Conc'])
    SlopeList = []
    i = 0

    #for i in range(DataLength - 1):
    while i < (DataLength-1):
        ydiff = filtered_df.iloc[i + 1, 2] - filtered_df.iloc[i, 2]
        xdiff = filtered_df.iloc[i + 1, 1] - filtered_df.iloc[i, 1]
        i = i + 1
        slope = abs(round(ydiff / xdiff, 2))
        SlopeList.append(slope)

    slope = float('nan')
    SlopeList.append(slope)

    # filtered_df['Slope'] = SlopeList
    filtered_df.loc[:, 'Slope'] = SlopeList

    # Detecting minimum slope point and estimating CMC concentration and CMC mole value
    # row_num = filtered_df[filtered_df['Slope'] == min(SlopeList)].index
    # print("row_num:", row_num)
    row_num = filtered_df[filtered_df['Slope'] == min(SlopeList)].index
    print("row_num:", row_num)
    
    if not row_num.empty:
        row_index = row_num[0]
        print("row_index:", row_index)

        print("DataFrame Size (rows, columns):", filtered_df.shape)
        if row_index < len(filtered_df):

            target_conc = filtered_df.iloc[row_index - 1, 1]
            #target_conc = filtered_df.iloc[row_num - 1, 1]
            target_cond = filtered_df.iloc[row_index - 1, 2]
            #target_cond = filtered_df.iloc[row_num - 1, 2]
            
            mole = filtered_df.iloc[row_index - 1, 3]
            #mole = filtered_df.iloc[row_num - 1, 3]
            target_molar = filtered_df.iloc[row_index - 1, 4]
            #target_molar = filtered_df.iloc[row_num - 1, 4]


            # Plotting graph of filtered dataframe
            fig, (ax1) = plt.subplots(1)
            filtered_df.plot(kind='scatter', x='Conc', y='Conductivity', ax=ax1)
            ax1.set_title("Concentration Verses Conductivity Graph")
            ax1.set_xlabel("Concentration")
            ax1.set_ylabel("Conductivity")
            ax1.legend()
            ax1.scatter(target_conc, target_cond, color='red', label='CMC Point')
            ax1.plot([target_conc, target_conc], [0, target_cond], color='gray', linestyle='--')
            ax1.plot([0, target_conc], [target_cond, target_cond], color='gray', linestyle='--')
            #filtered_df.plot(kind='scatter', x='ConRoot', y='Molar', ax=ax2)
            #ax2.set_title("Root of Concentration Verses Molar Conductance Graph")

            # Save plots as bytes
            img1 = BytesIO()
            plt.savefig(img1, format='png')
            #plt.savefig(img2, format='png')
            img1.seek(0)

            return {
                'result': filtered_df.to_html(),
                #'filtered_df': filtered_df,
                'plot1': base64.b64encode(img1.getvalue()).decode(),
                #'plot2': base64.b64encode(img2.getvalue()).decode(),
                'target_conc': target_conc,
                'target_cond': target_cond,
                'mole': mole,
                'target_molar': target_molar
            }
        else:
            print("Error: Row index is out of bounds.")
    else:
        print("No rows found with the minimum slope.")
        # Handle the case when there are no rows with the minimum slope
    # Handle the case when there are no rows with the minimum slope

@app.route('/data_analysis', methods=['GET', 'POST'])
def data_analysis():
    if request.method == 'POST':
        sample1 = float(request.form['sample1'])
        sample2 = float(request.form['sample2'])

        analysis_result = perform_surfactant_analysis(sample1, sample2)




        

        # Save plots as bytes
    



        return render_template('analysis_result.html', result=analysis_result)

    return render_template('data_analysis.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful', 'success')
    return redirect(url_for('login'))



if __name__ == '__main__':
    with app.app_context():

        db.create_all()
    app.run(debug=True)

