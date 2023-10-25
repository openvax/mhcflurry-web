from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
from dash.dash_table.Format import Format
import dash_bootstrap_components as dbc

import pandas as pd

import mhcflurry

PREDICTOR = mhcflurry.Class1PresentationPredictor.load()

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "MHCFlurry Web"
server = app.server


# define component sections
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
    stack = dbc.Stack([submit_button, download_button], direction="horizontal", gap=2)
    col = dbc.Col(stack, md=3)
    row = dbc.Row(col)
    div = html.Div(row)
    return div


def table_div():
    """Table of predictions"""
    header = html.H2(id="predictions-title")
    table = dash_table.DataTable(
        id="tbl",
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

# callbacks for interactivity
@callback(
    [
        Output("tbl", "data"),
        Output("tbl", "columns"),
        Output("predictions-title", "children"),
        Output("download-button", "style"),
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
    }
    if not n_clicks or not alleles or not peptides:
        return (
            output["table_data"],
            output["table_columns"],
            output["predictions-title"],
            output["download-button"],
        )

    peptides = peptides.split()
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
    invalid = peptides_df.loc[~peptides_df.valid].peptide
    # if len(invalid):
    #     output["is_open"] = True
    #     output["alert_children"] = f"Excluded {len(invalid)} unsupported peptides: {' '.join(invalid[:100])}"

    peptides = list(peptides_df.loc[peptides_df.valid].peptide)
    if not peptides:
        return output

    predictions = PREDICTOR.predict(
        peptides,
        alleles,
        include_affinity_percentile=True,
        verbose=False,
    )
    del predictions["peptide_num"]
    if (predictions["sample_name"] == predictions["best_allele"]).all():
        del predictions["sample_name"]

    output["table_data"] = predictions.to_dict("records")
    numeric_cols = predictions.select_dtypes(include="number").columns.tolist()
    output["table_columns"] = [
        dict(name=c.replace("_", " "), id=c, type="numeric", format=Format(precision=3))
        if c in numeric_cols
        else dict(name=c.replace("_", " "), id=c)
        for c in predictions.columns
    ]
    output["predictions-title"] = f"Predictions for {len(peptides)} peptides"
    output["download-button"] = dict()

    return (
        output["table_data"],
        output["table_columns"],
        output["predictions-title"],
        output["download-button"],
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


# utilities; TODO: move to a new file
def check_peptide_validity(peptides, min_length, max_length):
    valid_peptide_regex = "^[%s]{%d,%d}$" % (
        "".join(mhcflurry.amino_acid.COMMON_AMINO_ACIDS),
        min_length,
        max_length,
    )

    return pd.Series(peptides).str.match(valid_peptide_regex).values

# Assign app layout
app.layout = page_layout()

if __name__ == "__main__":
    app.run(debug=True)
