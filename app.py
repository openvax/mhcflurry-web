import socket

import pandas
from flask import Flask, render_template, request, flash, redirect, url_for

import mhcflurry
import mhcnames

from Bio import SeqIO

app = Flask(__name__)
app.secret_key = "this is mhcflurry secret key" + str(socket.gethostname())

PREDICTOR = mhcflurry.Class1PresentationPredictor.load()

from io import StringIO

_SOFTWARE_VERSIONS_STRING = ", ".join(
    "%s %s" % (module.__name__, getattr(module, '__version__'))
    for module in [
        mhcflurry, mhcnames
    ]
)


def check_peptide_validity(peptides, min_length, max_length):
    valid_peptide_regex = "^[%s]{%d,%d}$" % (
        "".join(mhcflurry.amino_acid.COMMON_AMINO_ACIDS), min_length, max_length)

    return pandas.Series(peptides).str.match(valid_peptide_regex).values


def predict_peptides(peptides, alleles):
    if not peptides:
        return None

    peptides_df = pandas.DataFrame({
        "peptide": peptides,
    })
    peptides_df["valid"] = check_peptide_validity(
        peptides,
        min_length=PREDICTOR.supported_peptide_lengths[0],
        max_length=PREDICTOR.supported_peptide_lengths[1],
    )
    invalid = peptides_df.loc[~peptides_df.valid].peptide
    if len(invalid):
        flash("Excluded %d unsupported peptides: %s" % (
            len(invalid), " ".join(invalid[:100])))

    peptides = list(peptides_df.loc[peptides_df.valid].peptide)
    if not peptides:
        return None

    predictions = PREDICTOR.predict(
        peptides,
        alleles,
        include_affinity_percentile=True,
        verbose=False)

    del predictions["peptide_num"]
    if (predictions["sample_name"] == predictions["best_allele"]).all():
        del predictions["sample_name"]

    return predictions


def predict_fasta(fasta_contents, alleles):
    if not fasta_contents.strip():
        return None
    protein_sequences = {
        record.id: str(record.seq) for record in
        SeqIO.parse(StringIO(fasta_contents), "fasta")
        if check_peptide_validity(
            str(record.seq),
            min_length=PREDICTOR.supported_peptide_lengths[0],
            max_length=10000)[0]
    }
    if not protein_sequences:
        return None
    predictions = PREDICTOR.predict_sequences(
        protein_sequences,
        alleles,
        result="all",
        verbose=False)
    return predictions


@app.route('/')
def main():
    return render_template(
        'index.html',
        mhcflurry_version=mhcflurry.__version__,
        alleles=sorted(
            PREDICTOR.supported_alleles,
            key=lambda a: (not a.startswith("HLA-"), a)))

@app.route('/results', methods=["POST", "GET"])
def get_results():
    if request.method == 'POST':
        form_alleles = request.form['alleles']
        form_peptides = request.form['peptides'].strip()
    else:
        form_alleles = request.args.get('alleles', "")
        form_peptides = request.args.get('peptides', "").strip()

    alleles = {
        str(genotype) : str(genotype).split(",")
        for genotype in form_alleles.split() if genotype
    }
    if not alleles:
        flash("Select at least one allele")
        return redirect(url_for('main'))

    max_len = 10000000
    if len(form_peptides) > max_len:
        form_peptides = form_peptides[:max_len]
        flash("Peptide/protein input truncated to %d bytes" % max_len)

    if not form_peptides:
        flash("Enter peptides or FASTA protein sequences")
        return redirect(url_for('main'))

    try:
        if ">" in form_peptides:
            raw_result_df = predict_fasta(form_peptides, alleles=alleles)
        else:
            raw_result_df = predict_peptides(
                form_peptides.upper().split(),
                alleles=alleles)
    except Exception as e:
        flash(str(e))
        app.logger.debug("User exception", exc_info=e)
        return redirect(url_for('main'))

    if raw_result_df is None or len(raw_result_df) == 0:
        flash("Your query resulted in no predictions.")
        return redirect(url_for('main'))
    else:
        result_df = raw_result_df
    return render_template(
        'result.html',
        software_note=_SOFTWARE_VERSIONS_STRING,
        mhcflurry_version=mhcflurry.__version__,
        result=result_df)

@app.route('/api-predict', methods=["POST", "GET"])
def iedb_api_predict():
    if request.method == 'POST':
        form_alleles = request.form['allele']
        form_peptides = request.form['peptide'].strip()
    else:
        form_alleles = request.args.get('allele', "")
        form_peptides = request.args.get('peptide', "").strip()

    alleles = {
        str(genotype): str(genotype).split(",") for genotype in
        form_alleles.split() if genotype
    }
    form_peptides = form_peptides.strip()[:10000000]
    peptides = [
        peptide.strip()
        for peptide in form_peptides.upper().split(",")
    ]
    if not peptides:
        return "ERROR: no peptide given"
    if not alleles:
        return "ERROR: no alleles given"

    try:
        result_df = predict_peptides(peptides, alleles=alleles)
        #result_df = result_df[["peptide", "length", "allele", "affinity"]]
    except ValueError as e:
        return "ERROR: %s" % e.args[0]
    return result_df.to_csv(sep="\t", index=False, float_format="%0.4f")


@app.route('/alleles', methods=["GET"])
def iedb_api_supported_alleles():
    peptide_lengths = ",".join(str(x) for x in range(
        PREDICTOR.supported_peptide_lengths[0],
        PREDICTOR.supported_peptide_lengths[1] + 1))
    strings = [
        "%s\t%s" % (allele, peptide_lengths)
        for allele in PREDICTOR.supported_alleles
    ]
    return "\n".join(strings)
