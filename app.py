from flask import Flask, render_template, request
from mhcflurry import Class1AffinityPredictor
from mhctools import MHCflurry
from Bio import SeqIO

app = Flask(__name__)
_predictor = Class1AffinityPredictor.load()

from io import StringIO


def predict_peptide(protein_sequence_list, alleles):
    predictor = MHCflurry(alleles=alleles)
    predictor.predictor = _predictor
    binding_predictions = predictor.predict_subsequences(protein_sequence_list,
        peptide_lengths=[9])
    
    prediction_scores = {
        (x.peptide, x.allele): x.affinity for x in binding_predictions
    }
    print(prediction_scores)
    return prediction_scores

def predict_fasta(fasta_contents, alleles):
    protein_sequences = {
        record.id: str(record.seq) for record in
        SeqIO.parse(StringIO(fasta_contents), "fasta")
    }
    return predict_peptide(protein_sequences, alleles)
    

def process_results(results, alleles):
    processed_result = {}
    for result in results:
        if result[0] not in processed_result:
            processed_result[result[0]] = [None] * len(alleles)
        processed_result[result[0]][alleles.index(result[1])] = results[result]
    return processed_result

@app.route('/')
def hello_world():
    return render_template('index.html', alleles=_predictor.supported_alleles)

@app.route('/results', methods=["POST"])
def get_results():

    peptide_type = "FASTA" if request.form['peptide_type'] == "fasta" else "peptide"

    alleles = request.form['alleles']
    alleles = alleles.split(';')
    alleles = [str(allele) for allele in alleles if allele != ""]
    result = None
    if peptide_type == "FASTA":
        result = predict_fasta(str(request.form['peptides']), alleles=alleles)
    else:
        result = predict_peptide([str(request.form['peptides'])], alleles=alleles)
    return render_template('result.html', result=process_results(result, alleles), alleles=alleles)


app.debug = True
app.run()