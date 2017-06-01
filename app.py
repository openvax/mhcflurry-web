from flask import Flask, render_template, request
import pandas
import numpy
import seaborn
import logging
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt  
import mhcflurry


app = Flask(__name__)

downloaded_predictor = mhcflurry.Class1AffinityPredictor.load()
print(downloaded_predictor.supported_alleles)


@app.route('/')
def hello_world():
    return render_template('index.html', alleles=downloaded_predictor.supported_alleles)

@app.route('/results', methods=["POST"])
def get_results():
    print(request.form['allele'])
    print(request.form['peptides'])
    allele = request.form['allele']
    peptides = request.form['peptides'].split(',')
    print(peptides)
    #print(downloaded_predictor.predict(allele="HLA-A0201", peptides=["SIINFEKL", "SIINFEQL"]))
    #print(downloaded_predictor.predict_to_dataframe(allele="HLA-A0201", peptides=["SIINFEKL", "SIINFEQL"]))
    # peptides=["SIINFEKL", "SIINFEQL"]
    return str(downloaded_predictor.predict(allele=allele, peptides=peptides))

app.run()


'''
paste ammino acid file ->


'''
