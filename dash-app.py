from io import StringIO
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
from dash.dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc

from Bio import SeqIO

import pandas as pd

import mhcflurry

PREDICTOR = mhcflurry.Class1PresentationPredictor.load()

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "MHCFlurry Web"
server = app.server


# Component sections
def header_div():
    """App intro"""
    header = html.H1(f"MHCFlurry Web {mhcflurry.__version__}")
    par = html.P(
        [
            "This prediction server generates MHC class I binding predictions using ",
            html.A("MHCFlurry", href="http://github.com/openvax/mhcflurry"),
            ".",
        ]
    )
    div = html.Div([header, par])
    return div


def alleles_input_div():
    """Alleles input, selected from a dropdown"""
    header = html.H2("Alleles")
    text = dbc.Label("Choose a bunch")
    dropdown = dcc.Dropdown(
        options=[a for a in sorted(PREDICTOR.supported_alleles)],
        multi=True,
        id="alleles-input",
    )
    col = dbc.Col([text, dropdown], md=6)
    row = html.Div([dbc.Row(col)])
    div = html.Div([header, row])
    return div


def peptides_input_div():
    """Peptides input, provided by the user in a textbox"""
    header = html.H2("Peptides")
    text = dbc.Label(
        "Enter whitespace-separated peptides, or a FASTA giving protein sequences"
    )
    example = dcc.Markdown(
        """
                                Example peptides:
                                ```
                                SIINFEKL SYYNFEKKL
                                ```
                                """
    )
    row_1 = dbc.Row(dbc.Col([text, example]))
    text_area = dbc.Textarea(
        id="peptides-input",
        placeholder="Enter peptides here",
        size="lg",
    )
    row_2 = dbc.Row(dbc.Col(text_area))
    div = html.Div([header, html.Div([row_1, row_2])])
    return div


def button_div():
    """Submit and download buttons"""
    submit_button = dbc.Button(
        "Submit", id="submit-button", className="me-1", n_clicks=0
    )
    download_button = dbc.Button(
        "Download",
        id="download-button",
        className="me-1",
        n_clicks=0,
        style=dict(display="none"),
        color="secondary",
    )
    horizontal_stack = dbc.Stack(
        [submit_button, download_button], direction="horizontal", gap=2
    )
    button_col = dbc.Col(horizontal_stack, md=3)
    alert = dbc.Alert(
        "",
        id="submit-alert",
        is_open=False,
        dismissable=True,
        fade=False,
    )
    alert_col = dbc.Col(alert, md=6)
    row = dbc.Row([button_col, alert_col])
    div = html.Div(row)
    return div


def table_div():
    """Table of predictions"""
    header = html.H2(id="predictions-title")
    table = dash_table.DataTable(
        id="tbl",
        sort_action="native",
        page_action="native",
        page_size=100,
        style_data={
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_header={
            "whiteSpace": "normal",
            "height": "auto",
        },
    )
    row = dbc.Row(dbc.Col(table))
    spinner = dbc.Spinner(row, id="predictions-spinner")
    div = html.Div([header, spinner])
    return div


def page_layout():
    stacked_sections = dbc.Stack(
        [
            alleles_input_div(),
            html.Br(),
            peptides_input_div(),
            html.Br(),
            button_div(),
            html.Br(),
            table_div(),
        ],
        gap=3,
    )
    container = dbc.Container(
        [
            header_div(),
            html.Hr(),
            stacked_sections,
            dcc.Download(id="download-dataframe-csv"),
        ]
    )
    return container


# Callbacks for interactivity
@callback(
    [
        Output("tbl", "data"),
        Output("tbl", "columns"),
        Output("predictions-title", "children"),
        Output("download-button", "style"),
        Output("submit-alert", "is_open"),
        Output("submit-alert", "children"),
    ],
    inputs=[Input("submit-button", "n_clicks")],
    state=[State("peptides-input", "value"), State("alleles-input", "value")],
    prevent_initial_call=True,
)
def update_table(n_clicks, peptides, alleles):
    output = {
        "table_data": [],
        "table_columns": [],
        "predictions-title": "",
        "download-button": dict(display="none"),
        "submit-alert-open": False,
        "submit-alert-children": "",
    }
    if not n_clicks or not alleles or not peptides:
        if not alleles:
            output["submit-alert-children"] = "Please select at least one allele"
            output["submit-alert-open"] = True
        if not peptides:
            output["submit-alert-children"] = "Please enter at least one peptide"
            output["submit-alert-open"] = True
        return (
            output["table_data"],
            output["table_columns"],
            output["predictions-title"],
            output["download-button"],
            output["submit-alert-open"],
            output["submit-alert-children"],
        )

    try:
        if ">" in peptides:
            # we have a FASTA
            predictions, invalid = predict_fasta(peptides, alleles=alleles)
        else:
            predictions, invalid = predict_peptides(peptides, alleles)

        if invalid:
            invalid_str = ", ".join(invalid)
            if len(invalid_str) > 100:
                invalid_str = invalid_str[:100] + "..."
            output[
                "submit-alert-children"
            ] = f"Excluded invalid peptides: {invalid_str}"
            output["submit-alert-open"] = True
    except:
        output[
            "submit-alert-children"
        ] = "An error occurred. Please check your inputs and try again."
        output["submit-alert-open"] = True
        return output

    if predictions.empty:
        return (
            output["table_data"],
            output["table_columns"],
            output["predictions-title"],
            output["download-button"],
            output["submit-alert-open"],
            output["submit-alert-children"],
        )
    output["table_data"] = predictions.to_dict("records")

    def _format_column(col, numeric_cols):
        if col == "pos":
            return dict(
                name=col.replace("_", " "),
                id=col,
                type="numeric",
                format=Format(precision=3, scheme=Scheme.decimal_integer),
            )
        if col in numeric_cols:
            return dict(
                name=col.replace("_", " "),
                id=col,
                type="numeric",
                format=Format(precision=3, scheme=Scheme.fixed),
            )
        else:
            return dict(name=col.replace("_", " "), id=col)

    numeric_cols = predictions.select_dtypes(include="number").columns.tolist()
    output["table_columns"] = [
        _format_column(c, numeric_cols) for c in predictions.columns
    ]

    output["predictions-title"] = f"Predictions for {len(peptides)} peptides"
    output["download-button"] = dict()

    return (
        output["table_data"],
        output["table_columns"],
        output["predictions-title"],
        output["download-button"],
        output["submit-alert-open"],
        output["submit-alert-children"],
    )


@callback(
    Output("download-dataframe-csv", "data"),
    inputs=[Input("download-button", "n_clicks")],
    state=[State("tbl", "data"), State("tbl", "columns")],
    prevent_initial_call=True,
)
def download_table(n_clicks, data, columns):
    if not n_clicks:
        return None
    df = pd.DataFrame(data, columns=[c["id"] for c in columns])
    return dcc.send_data_frame(df.to_csv, "mhcflurry-predictions.csv")


# Utility methods
# TODO: move to a new file
def check_peptide_validity(peptides, min_length, max_length):
    valid_peptide_regex = "^[%s]{%d,%d}$" % (
        "".join(mhcflurry.amino_acid.COMMON_AMINO_ACIDS),
        min_length,
        max_length,
    )

    return pd.Series(peptides).str.match(valid_peptide_regex).values


def predict_peptides(peptides, alleles):
    invalid = []
    peptides = peptides.upper().split()
    peptides_df = pd.DataFrame(
        {
            "peptide": peptides,
        }
    )
    peptides_df["valid"] = check_peptide_validity(
        peptides,
        min_length=PREDICTOR.supported_peptide_lengths[0],
        max_length=PREDICTOR.supported_peptide_lengths[1],
    )
    invalid = peptides_df.loc[~peptides_df.valid].peptide.tolist()

    peptides = list(peptides_df.loc[peptides_df.valid].peptide)
    if not peptides:
        return pd.DataFrame(), invalid

    predictions = PREDICTOR.predict(
        peptides,
        alleles,
        include_affinity_percentile=True,
        verbose=False,
    )
    del predictions["peptide_num"]
    if (predictions["sample_name"] == predictions["best_allele"]).all():
        del predictions["sample_name"]

    return predictions, invalid


def predict_fasta(fasta_contents, alleles):
    protein_sequences = {
        record.id: str(record.seq)
        for record in SeqIO.parse(StringIO(fasta_contents), "fasta")
        if check_peptide_validity(
            str(record.seq),
            min_length=PREDICTOR.supported_peptide_lengths[0],
            max_length=10000,
        )[0]
    }
    if not protein_sequences:
        return pd.DataFrame(), fasta_contents

    predictions = PREDICTOR.predict_sequences(
        protein_sequences, alleles, result="all", verbose=False
    )

    return predictions, []


# Assign app layout
app.layout = page_layout()

if __name__ == "__main__":
    app.run(debug=True)
