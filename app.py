import pandas
from flask import Flask, render_template, request, flash, redirect, url_for

import mhcflurry
import mhcnames
import mhctools

from mhcflurry import Class1AffinityPredictor, amino_acid
from mhctools import MHCflurry
from Bio import SeqIO

app = Flask(__name__)
app.secret_key = "this is mhcflurry secret key"
_predictor = Class1AffinityPredictor.load()

from io import StringIO

_SOFTWARE_VERSIONS_STRING = ", ".join(
    "%s %s" % (module.__name__, getattr(module, '__version__'))
    for module in [
        mhcflurry, mhcnames, mhctools
    ]
)


def check_peptide_validity(peptides, min_length, max_length):
    valid_peptide_regex = "^[%s]{%d,%d}$" % (
        "".join(amino_acid.COMMON_AMINO_ACIDS), min_length, max_length)

    return pandas.Series(peptides).str.match(valid_peptide_regex).values


def predict_peptide(peptides, alleles):
    if not peptides:
        return None

    peptides_df = pandas.DataFrame({
        "peptide": peptides,
    })
    peptides_df["valid"] = check_peptide_validity(
        peptides,
        min_length=_predictor.supported_peptide_lengths[0],
        max_length=_predictor.supported_peptide_lengths[1],
    )
    invalid = peptides_df.loc[~peptides_df.valid].peptide
    if len(invalid):
        flash("Excluded %d unsupported peptides: %s" % (
            len(invalid), " ".join(invalid[:100])))

    peptides = list(peptides_df.loc[peptides_df.valid].peptide)
    if not peptides:
        return None

    predictor = MHCflurry(alleles=alleles)
    predictor.predictor = _predictor
    binding_predictions = predictor.predict_peptides(peptides).to_dataframe()
    return binding_predictions


def predict_fasta(fasta_contents, alleles):
    if not fasta_contents.strip():
        return None
    protein_sequences = {
        record.id: str(record.seq) for record in
        SeqIO.parse(StringIO(fasta_contents), "fasta")
        if check_peptide_validity(
            str(record.seq),
            min_length=_predictor.supported_peptide_lengths[0],
            max_length=10000)[0]
    }
    if not protein_sequences:
        return None
    predictor = MHCflurry(alleles=alleles)
    binding_predictions = predictor.predict_subsequences(
        protein_sequences,
        peptide_lengths=range(
            _predictor.supported_peptide_lengths[0],
            _predictor.supported_peptide_lengths[1] + 1,
        )).to_dataframe()
    print(binding_predictions)
    return binding_predictions


@app.route('/')
def main():
    return render_template(
        'index.html',
        mhcflurry_version=mhcflurry.__version__,
        alleles=_predictor.supported_alleles)

@app.route('/results', methods=["POST"])
def get_results():
    alleles = [
        str(allele) for allele in request.form['alleles'].split() if allele
    ]
    if not alleles:
        flash("Select at least one allele")
        return redirect(url_for('main'))

    if not request.form['peptides'].strip():
        flash("Enter peptides or FASTA protein sequences")
        return redirect(url_for('main'))

    form_peptides = request.form['peptides'].strip()[:10000000]  # limit the length

    try:
        if ">" in request.form['peptides']:
            raw_result_df = predict_fasta(
                form_peptides, alleles=alleles)
        else:
            raw_result_df = predict_peptide(
                form_peptides.upper().split(), alleles=alleles)
    except Exception as e:
        flash(str(e))
        return redirect(url_for('main'))

    if raw_result_df is None or len(raw_result_df) == 0:
        result_df = pandas.DataFrame(
            columns=["peptide", "length", "tightest_affinity"])
        flash("Your query resulted in no predictions.")
        return redirect(url_for('main'))
    else:
        result_df = raw_result_df.drop_duplicates(["peptide", "allele"]).reset_index()
        result_df = result_df.pivot(index="peptide", columns="allele", values="affinity")
        result_df = result_df.reset_index()

        result_df["tightest_affinity"] = result_df.min(1)
        result_df["length"] = result_df.peptide.str.len()
        front_cols = ["peptide", "length", "tightest_affinity"]
        allele_cols = [c for c in result_df.columns if c not in front_cols]
        full_cols = front_cols + allele_cols
        result_df = result_df[full_cols].sort_values("tightest_affinity")
        if len(allele_cols) == 1:
            del result_df["tightest_affinity"]
        print(result_df)
    return render_template(
        'result.html',
        software_note=_SOFTWARE_VERSIONS_STRING,
        mhcflurry_version=mhcflurry.__version__,
        result=result_df)


app.debug = True
app.run()