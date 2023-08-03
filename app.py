from flask import Flask, request, render_template, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FileField, IntegerField, FloatField
from wtforms.validators import DataRequired, NumberRange
from werkzeug.utils import secure_filename
import pandas as pd

global_portfolio_df = None
global_csm_scores_df = None

stages = { ## weight for each stage of the customer journey
    "Onboarding": 3.5,
    "Adoption": 2.5,
    "Value Realization": 1.5,
    "Renewal": 0.5,
    "Self-Sufficent": 0.25,
}

license_bands = { ## weight for each license count band
    range(0, 99): 1,
    range(100, 249): 1.25,
    range(250, 499): 1.5,
    range(500, 999): 2,
    range(1000, 9999999): 2.5,
}

timezones = {
    "US-East": [-5, -4],
    "US-West": [-8, -7],
    "US-Central": [-6, -5],
    "US-Mountain": [-7, -6],
    "EU-West": [0, 1],
    "EU-Central": [1, 2],
    "EU-East": [2, 3],
    "Australia-West": [8, 9],
    "Australia-Central": [9, 10],
    "Australia-East": [10, 11],
    "India": [5.5, 6.5],
    "Japan": [9, 10],
    "China": [8, 9],
}

def get_license_band_weight(licenses):
    for band, weight in license_bands.items():
        if licenses in band:
            return weight

def get_stage_weight(stage):
    return stages[stage]

def import_csv(file):
    if file is None:
        return None
    else:
        df = pd.read_csv(file, encoding='iso-8859-1')
        return df

csms = [ ## base info for each CSM, i.e. name, language, timezone
    {
        "name": "Chris O'Hara",
        "language": "English",
        "timezone": "UTC-6",
    },
    {
        "name": "Elizabeth Pickel",
        "language": "English",
        "timezone": "UTC-5",
    },
    {
        "name": "Hannah Bridges",
        "language": "English",
        "timezone": "UTC-5",
    },
    {
        "name": "Ian Mai",
        "language": "English",
        "timezone": "UTC-6",
    },
    {
        "name": "Jeffrey Nadeau",
        "language": "English",
        "timezone": "UTC-5",
    },
    {
        "name": "John Potts",
        "language": "English",
        "timezone": "UTC+0",
    },
    {
        "name": "Josh Trota",
        "language": "English",
        "timezone": "UTC-5",
    },
    {
        "name": "MK Sullivan",
        "language": "English",
        "timezone": "UTC-5",
    },
    {
        "name": "Michael Lunzer",
        "language": "English",
        "timezone": "UTC-8",
    },
    {
        "name": "Paula Kim",
        "language": "English",
        "timezone": "UTC-8",
    },
    {
        "name": "Priyankha B",
        "language": "English",
        "timezone": "UTC+5.5",
    },
    {
        "name": "Sachin Khalsa",
        "language": "English",
        "timezone": "UTC-5",
    },
    {
        "name": "Tony Cina",
        "language": "English",
        "timezone": "UTC-5",
    }
]

time_zones = {
    "UTC-10": "Hawaii (UTC-10)",
    "UTC-9": "Alaska (UTC-9)",
    "UTC-8": "Pacific Time (US & Canada) (UTC-8)",
    "UTC-7": "Mountain Standard Time (UTC-7)",
    "UTC-6": "Central Standard Time (UTC-6)",
    "UTC-5": "Eastern Standard Time (UTC-5)",
    "UTC-4": "Atlantic Standard Time (UTC-4)",
    "UTC-3": "Greenland Standard Time (UTC-3)",
    "UTC-2": "Fernando de Noronha Time (UTC-2)",
    "UTC-1": "Azores Standard Time (UTC-1)",
    "UTC+0": "Greenwich Mean Time (UTC+0)",
    "UTC+1": "Central European Time (UTC+1)",
    "UTC+2": "Eastern European Time (UTC+2)",
    "UTC+3": "Moscow Standard Time (UTC+3)",
    "UTC+4": "Samara Standard Time (UTC+4)",
    "UTC+5": "Pakistan Standard Time (UTC+5)",
    "UTC+5.5": "Indian Standard Time (UTC+5:30)",
    "UTC+6": "Bangladesh Standard Time (UTC+6)",
    "UTC+7": "Indochina Time (UTC+7)",
    "UTC+8": "China Standard Time (UTC+8)",
    "UTC+9": "Japan Standard Time (UTC+9)",
    "UTC+10": "Australian Eastern Standard Time (UTC+10)",
    "UTC+11": "Vanuatu Standard Time (UTC+11)",
    "UTC+12": "Fiji Time (UTC+12)",
}

time_zone_choices = [(k, v) if not isinstance(v, list) else (k, ', '.join(v)) for k, v in time_zones.items()]

csm_info_df = pd.DataFrame(csms) ## creates dataframe from base info from each CSM, i.e. name, language, timezone

def get_cust_bandwidth_score(row):
    score = get_stage_weight(row["stage"]) * get_license_band_weight(row["licenses"])
    return score

def get_csm_timezone(csm):
    for csm in csms:
        if csm["name"] == csm:
            return csm["timezone"]
        
def get_csm_language(csm):
    for csm in csms:
        if csm["name"] == csm:
            return csm["language"]
        
def recommend_csm(cust_language, cust_timezone, cust_industry, csm_info_df, csm_scores_df, portfolio_df):

    # Convert the customer timezone to numerical format (excluding "UTC")
    cust_timezone = float(cust_timezone.replace('UTC', ''))

    # Filter CSMs that speak the same language as the customer
    possible_csms = csm_info_df[csm_info_df['language'] == cust_language]

    # Convert CSMs' timezone to numerical format (excluding "UTC") and calculate the difference
    possible_csms['timezone_diff'] = possible_csms['timezone'].apply(lambda x: abs(float(x.replace('UTC', '')) - cust_timezone))

    # Filter CSMs that are within 3 timezones of the customer
    possible_csms = possible_csms[possible_csms['timezone_diff'] <= 3]

    # Join the possible CSMs with their bandwidth scores
    possible_csms = possible_csms.merge(csm_scores_df, left_on='name', right_on='csm')

    # Count the number of customers in the same industry for each CSM
    industry_counts = portfolio_df[portfolio_df['industry'] == cust_industry].groupby('csm').size().reset_index(name='industry_count')

    # Join the possible CSMs with their industry counts
    possible_csms = possible_csms.merge(industry_counts, on='csm', how='left').fillna(0)

    # Add a new score that gives additional preference to CSMs with more customers in the same industry
    # (you can adjust the weights to suit your needs)
    possible_csms['score'] = possible_csms['bandwidth_score'] - 0.1 * possible_csms['industry_count']

    # Store the industry count in the dataframe
    possible_csms['industry_weight'] = possible_csms['industry_count']

    # Choose the CSM with the lowest score
    recommended_csm = possible_csms[possible_csms['score'] == possible_csms['score'].min()]
    recommended_csm = recommended_csm[['name', 'language', 'timezone', 'industry_count']]

    return recommended_csm
        
## Define Form

class IncomingCustomer(FlaskForm):
    cust_name = StringField('Customer Name', validators=[DataRequired()])
    cust_language = SelectField('Spoken Language', choices=[('English', 'English'), 
                                                     ('Spanish', 'Spanish'), 
                                                     ('French', 'French'), 
                                                     ('German', 'German'), 
                                                     ('Portuguese', 'Portuguese'), 
                                                     ('Italian', 'Italian'), 
                                                     ('Hapanese', 'Japanese'), 
                                                     ('Korean', 'Korean'), 
                                                     ('Chinese', 'Chinese'), 
                                                     ('Hebrew', 'Hebrew'), 
                                                     ('Arabic', 'Arabic')], 
                                                     validators=[DataRequired()])
    cust_timezone = SelectField('Timezone', choices=time_zone_choices, validators=[DataRequired()])
                                                    # [
                                                    #  ('et', 'US-East'), 
                                                    #  ('ct', 'US-Central'), 
                                                    #  ('mt', 'US-Mountain'), 
                                                    #  ('pt', 'US-Pacific'), 
                                                    #  ('hst', 'US-Hawaii'), 
                                                    #  ('akst', 'US-Alaska'), 
                                                    #  ('bst', 'UK'), 
                                                    #  ('cest', 'Europe'), 
                                                    #  ('aet', 'Austraila-East'),  
                                                    #  ('act', 'Australia-Central'), 
                                                    #  ('awt', 'Australia-West'), 
                                                    #  ('it', 'India'), 
                                                    #  ('sgt', 'Singapore'), 
                                                    #  ('hkt', 'Hong Kong'), 
                                                    #  ('jst', 'Japan'), 
                                                    #  ('nzt', 'New Zealand Daylight Time')
                                                    #  ], 
                                                    #  validators=[DataRequired()])
    cust_licenses = IntegerField('# of Licenses', validators=[DataRequired(), NumberRange(min=1, max=100000, message='Must be greater than 0')])
    cust_industry = StringField('Industry', validators=[DataRequired()])
    submit = SubmitField('Get CSM Assignment')

class UploadCSV(FlaskForm):
    csv_file = FileField('Upload CSV', validators=[DataRequired()])
    submit = SubmitField('Calculate Current Bandwidth')

class CSM_Data(FlaskForm):
    csv_file = FileField('Upload CSV', validators=[DataRequired()])
    submit = SubmitField('Import CSM Data')
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcd'

@app.route('/', methods=['GET', 'POST'])

def index():
    incoming_customer_form = IncomingCustomer()
    upload_csv_form = UploadCSV()
    upload_csm_data_form = CSM_Data()

    show_modal_csm = False
    show_modal = False

    ## Initialize variables
    global global_portfolio_df
    global global_csm_scores_df
    global global_csm_data_df

    portfolio_df = csm_scores_df = recommended_csm = recommended_csm_info = recommended_csm_dict = cust_name = cust_language = cust_timezone = None
    cust_licenses = 0
    full_portfolio_df = None

    if upload_csm_data_form.validate_on_submit():
        csm_data_file = upload_csm_data_form.csv_file.data
        csm_data_df = pd.read_csv(csm_data_file)
        global_csm_data_df = csm_data_df

    if incoming_customer_form.validate_on_submit():
        cust_name = incoming_customer_form.cust_name.data
        cust_language = incoming_customer_form.cust_language.data
        cust_timezone = incoming_customer_form.cust_timezone.data
        cust_licenses = incoming_customer_form.cust_licenses.data
        cust_industry = incoming_customer_form.cust_industry.data

        portfolio_df = global_portfolio_df
        csm_scores_df = global_csm_scores_df
        
        recommended_csm = recommend_csm(cust_language, cust_timezone, cust_industry, csm_info_df, csm_scores_df, portfolio_df)
        recommended_csm_dict = recommended_csm.to_dict(orient='records') # convert recommended CSM to dict

        show_modal_csm = True
    
    else:
        show_modal_csm = False

    if upload_csv_form.validate_on_submit():
        import_file = upload_csv_form.csv_file.data
        portfolio_data = pd.read_csv(import_file, encoding='iso-8859-1') # reads the CSV file and converts to a dataframe. Requires encoding to read special characters
        full_portfolio_df = portfolio_data
        
        full_portfolio_df = full_portfolio_df.rename(columns= { ## renames columns to match the formulas below. Just for ease of use
            "Key Domain":"domain",
            "CSM":"csm",
            "Account Name":"account",
            "# of Licenses":"licenses",
            "Customer Journey Stage":"stage",
            "Language":"language",
            "Timezone":"timezone",
            "Account: Account Name":"account", 
            "Postman Team: Postman Team Name":"name", 
            "Account: Industry":"industry", 
            "Account: CSM":"csm",
            "Account: Stage":"stage",
            "Active Plan":"plan",
            "Account: # of Paid Team Licenses (Account)":"licenses",
            "Account: Language":"language",
            }
        )

        ## Create new columns for the portfolio dataframe if they don't already exist
        if "stage" not in full_portfolio_df.columns: 
            full_portfolio_df["stage"] = "Onboarding"
        if "language" not in full_portfolio_df.columns:
            full_portfolio_df["language"] = "English"
        if "timezone" not in full_portfolio_df.columns:
            full_portfolio_df["timezone"] = "US-East"

        ## pull the columns we need from the full portfolio dataframe
        portfolio_df = full_portfolio_df[["csm", "domain", "stage", "licenses", "industry", "language", "timezone"]]

        ## do the calculations for the bandwidth score and store them in the dataframe
        portfolio_df["band_weight"] = portfolio_df["licenses"].apply(get_license_band_weight) 
        portfolio_df["stage_weight"] = portfolio_df["stage"].apply(get_stage_weight)
        portfolio_df["bandwidth_score"] = portfolio_df["band_weight"] * portfolio_df["stage_weight"]

        ## create a new dataframe that groups by CSM and sums the bandwidth scores
        csm_scores_df = portfolio_df.groupby("csm")["bandwidth_score"].sum() 
        csm_scores_df = csm_scores_df.reset_index() ## resets the index so that the CSM name is a column

        ## show the popup modal in the web app
        show_modal = True
        csm_scores_dict = csm_scores_df.to_dict(orient='records')

        global_portfolio_df = portfolio_df
        global_csm_scores_df = csm_scores_df

    else:
        
        show_modal = False
        csm_scores_dict = None

    # pass the variables to the web app
    return render_template('index.html', recommended_csm_dict=recommended_csm_dict, recommended_csm_info=recommended_csm_info, csm_scores_dict=csm_scores_dict, show_modal=show_modal, show_modal_csm=show_modal_csm, IncomingCustomer=incoming_customer_form, cust_name=cust_name, cust_language=cust_language, cust_timezone=cust_timezone, cust_licenses=cust_licenses, csm_scores_df=csm_scores_df, csm_info_df=csm_info_df, portfolio_df=portfolio_df, full_portfolio_df=full_portfolio_df, UploadCSV=upload_csv_form)
    
if __name__ == "__main__":
    app.run(debug=False)