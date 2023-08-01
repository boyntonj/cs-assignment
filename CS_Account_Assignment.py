# from flask import Flask, request, render_template, flash, session
# from flask_wtf import FlaskForm
# from wtforms import StringField, SubmitField, SelectField, FileField
# from wtforms.validators import DataRequired
# from werkzeug.utils import secure_filename
import pandas as pd

# import_file = None

import_file = "./test_csv.csv" #import data csv from root folder

stages = { ## weight for each stage of the customer journey
    "Onboarding": 3.5,
    "Adoption": 3,
    "Value Realization": 1.5,
    "Maintenance": 0.25,
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

# portfolio = [ # Dummy Portfolio data for testing
#                 {
#                 "name": "Customer1",
#                 "stage": "Maintenance",
#                 "licenses": 1000,
#                 "industry": "Technology",
#                 "timezone": "US-East",
#                 "csm": "CSM1",
#                 },
#                 {
#                 "name": "Customer2",
#                 "stage": "Adoption",
#                 "licenses": 200,
#                 "industry": "Technology",
#                 "timezone": "US-East",
#                 "csm": "CSM1",
#                 },
#                 {
#                 "name": "Customer3",
#                 "stage": "Onboarding",
#                 "licenses": 100,
#                 "industry": "Technology",
#                 "timezone": "US-East",
#                 "csm": "CSM1",
#                 },
#                 {
#                 "name": "Customer4",
#                 "stage": "Adoption",
#                 "licenses": 200,
#                 "industry": "Technology",
#                 "timezone": "US-East",
#                 "csm": "CSM3",
#                 },
#                 {
#                 "name": "Customer5",
#                 "stage": "Onboarding",
#                 "licenses": 10000,
#                 "industry": "Technology",
#                 "timezone": "US-East",
#                 "csm": "CSM2",
#                 },
#                 {
#                 "name": "Customer6",
#                 "stage": "Adoption",
#                 "licenses": 500,
#                 "industry": "Technology",
#                 "timezone": "US-East",
#                 "csm": "CSM1",
#                 },
            
# ] 

csms = [ ## base info for each CSM, i.e. name, language, timezone
    {
        "name": "CSM1",
        "language": "English",
        "timezone": "US-East",
    },
    {
        "name": "CSM2",
        "language": "English",
        "timezone": "US-East",
    },
    {
        "name": "CSM3",
        "language": "English",
        "timezone": "US-East",
    }
]

def get_cust_bandwidth_score(row):
    score = get_stage_weight(row["stage"]) * get_license_band_weight(row["licenses"])
    return score

def set_customer_bandwidths():
    for customer in portfolio_data:
        score = get_cust_bandwidth_score(customer)
        customer["bandwidth"] = score

def set_csm_bandwidths():
    for customer in portfolio_data:
        for csm in csms:
            if customer["csm"] == csm["name"]:
                if "bandwidth" not in csm:
                    csm["bandwidth"] = 0
                    score = get_cust_bandwidth_score(customer)
                    csm["bandwidth"] = csm["bandwidth"] + score 
                else: 
                    score = get_cust_bandwidth_score(customer)
                    csm["bandwidth"] = csm["bandwidth"] + score  

if import_file is not None:
    portfolio_data = import_csv(import_file)
    full_portfolio_df = portfolio_data
else:
    portfolio_data = portfolio

# set_customer_bandwidths()
# set_csm_bandwidths()

csm_info_df = pd.DataFrame(csms) ## creates dataframe from base info from each CSM, i.e. name, language, timezone
full_portfolio_df = full_portfolio_df.rename(columns= { 
            "Key Domain":"domain",
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

if "stage" not in full_portfolio_df.columns:
    full_portfolio_df["stage"] = "Onboarding"
if "language" not in full_portfolio_df.columns:
    full_portfolio_df["language"] = "English"
if "timezone" not in full_portfolio_df.columns:
    full_portfolio_df["timezone"] = "US-East"

portfolio_df = full_portfolio_df[["csm", "domain", "stage", "licenses", "industry", "language", "timezone"]]

portfolio_df["band_weight"] = portfolio_df["licenses"].apply(get_license_band_weight)
portfolio_df["stage_weight"] = portfolio_df["stage"].apply(get_stage_weight)
portfolio_df["bandwidth_score"] = portfolio_df["band_weight"] * portfolio_df["stage_weight"]

csm_scores_df = portfolio_df.groupby("csm")["bandwidth_score"].sum()
csm_scores_df = csm_scores_df.reset_index()

print(portfolio_df, "\n") # prints tweaked dataframe of all accounts and their scores
print(csm_scores_df, "\n")
# print(f"CSMs\n", csm_info_df, "\n")
