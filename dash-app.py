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

# App layout
header_div = html.Div(
    [
        html.H1(f"MHCFlurry Web {mhcflurry.__version__}"),
        html.Div(
            [
                html.P(
                    [
                        "This prediction server generates MHC class I binding predictions using ",
                        html.A("MHCFlurry", href="http://github.com/openvax/mhcflurry"),
                        ".",
                    ]
                ),
            ]
        ),
    ]
)

alleles_input_div = html.Div(
    [
        html.H2("Alleles"),
        html.Div(
            [
                dbc.Row(
                    dbc.Col(
                        [
                            dbc.Label("Choose a bunch"),
                            dcc.Dropdown(
                                options=[
                                    a for a in sorted(PREDICTOR.supported_alleles)
                                ],
                                multi=True,
                                id="alleles-input",
                            ),
                        ],
                        md=6,
                    )
                ),
            ]
        ),
    ]
)

peptides_input_div = html.Div(
    [
        html.H2("Peptides"),
        html.Div(
            [
                dbc.Row(
                    dbc.Col(
                        [
                            dbc.Label(
                                "Enter whitespace-separated peptides, or a FASTA giving protein sequences"
                            ),
                            dcc.Markdown(
                                """
            Example peptides:
            ```
            SIINFEKL SYYNFEKKL
            ```
            """
                            ),
                        ]
                    )
                ),
                dbc.Row(
                    dbc.Col(
                        [
                            dbc.Textarea(
                                id="peptides-input",
                                placeholder="Enter peptides here",
                                size="lg",
                            ),
                        ],
                    )
                ),
            ]
        ),
    ]
)

button_div = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Stack(
                        [
                            dbc.Button(
                                "Submit",
                                id="submit-button",
                                className="me-1",
                                n_clicks=0,
                            ),
                            dbc.Button(
                                "Download",
                                id="download-button",
                                className="me-1",
                                n_clicks=0,
                                style=dict(display="none"),
                                color="secondary"
                            ),
                        ],
                        direction="horizontal", gap=2
                    ),
                    md=3,
                )
            ]
        )
    ]
)

table_div = html.Div(
    [
        html.H2(id="predictions-title"),
        dbc.Row(
            dbc.Col(
                dash_table.DataTable(
                    id="tbl",
                    style_data={
                        "whiteSpace": "normal",
                        "height": "auto",
                    },
                    style_header={
                        "whiteSpace": "normal",
                        "height": "auto",
                    },
                ),
            )
        ),
    ]
)

app.layout = dbc.Container(
    [
        header_div,
        html.Hr(),
        dbc.Stack(
            [
                alleles_input_div,
                html.Br(),
                peptides_input_div,
                html.Br(),
                button_div,
                html.Br(),
                table_div,
            ],
            gap=3,
        ),
        dcc.Download(id="download-dataframe-csv"),
    ]
)


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

    print(peptides)
    print(alleles)

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


def check_peptide_validity(peptides, min_length, max_length):
    valid_peptide_regex = "^[%s]{%d,%d}$" % (
        "".join(mhcflurry.amino_acid.COMMON_AMINO_ACIDS),
        min_length,
        max_length,
    )

    return pd.Series(peptides).str.match(valid_peptide_regex).values

@callback(
    Output("download-dataframe-csv", "data"),
    inputs=[Input("download-button", "n_clicks")],
    state=[State("tbl", "data"), State("tbl", "columns")],
    prevent_initial_call=True,
)
def download_table(n_clicks, data, columns):
    if not n_clicks:
        return None
    print(data)
    print(columns)
    df = pd.DataFrame(data, columns=[c["id"] for c in columns])
    print(df)
    return dcc.send_data_frame(df.to_csv, "mhcflurry-predictions.csv")


if __name__ == "__main__":
    app.run(debug=True)
