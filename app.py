from flask import Flask, render_template, request
from mhcflurry import Class1AffinityPredictor
from mhctools import MHCflurry
from Bio import SeqIO
from io import StringIO
from flask_wtf import Form
from wtforms import *
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea


app = Flask(__name__)
_predictor = Class1AffinityPredictor.load()


peptide_length_choices = [(str(i), str(i)) for i in range(8, 15)]
peptide_length_choices = [('all', 'all')] + peptide_length_choices

allele_choices = [(str(i), str(i)) for i in _predictor.supported_alleles]

class MHCFlurry_Form(Form):
    peptide_input_type = SelectField("Input Type",
        choices=[('fasta', 'FASTA'), ('peptide', 'Peptide')],
        validators=[validators.InputRequired()],
    )

    peptide_contents = StringField("Input File", widget=TextArea())

    selected_alleles = StringField("Selected Alleles")

    peptide_length = SelectField("Peptide Length",
        choices=peptide_length_choices,
        validators=[validators.InputRequired()],
    )

    allele = SelectField("Allele Choices",
        choices=allele_choices,
        validators=[validators.InputRequired()],
    )

    selected_alleles = StringField('Selected Alleles')

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
def index():
    return render_template('index.html', alleles=_predictor.supported_alleles, form=MHCFlurry_Form())    

@app.route('/results', methods=["POST"])
def get_results():

    try:
        form = MHCFlurry_Form(request.form)
        print("a")
        if not form.validate():
            return "invalid form"
        print("a")

        peptide_type = form.peptide_input_type.data
        print("a")

        alleles = form.selected_alleles.data
        print("a")
        alleles = alleles.split(';')
        print("a")
        alleles = [str(allele) for allele in alleles if allele != ""]
        result = None
        print("a")
        print(peptide_type)
        if peptide_type == "fasta":
            print("blah")
            result = predict_fasta(str(form.peptide_contents.data), alleles=alleles)
        else:
            result = predict_peptide([str(form.peptide_contents.data)], alleles=alleles)
        print("z")
        return render_template('result.html', result=process_results(result, alleles), alleles=alleles)
    except Exception as e:
        return str(e)

app.debug = True
app.run()
