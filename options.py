import datetime
import decimal
import os
from enum import Enum
import math
from itertools import chain

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots

from options_math import (
    return_call_array,
    return_covered_call_array,
    return_covered_cash_covered_put_array,
    return_put_array,
)

tiingo_api_key = os.getenv("TIINGO_API_KEY")
if tiingo_api_key == None:
    raise EnvironmentError(
        """Missing TIINGO_API_KEY, please set this environment variable."""
    )

DEFAULT_STYLE = {
    "display": "inline-block",
    "flex-wrap": "wrap",
    "padding-right": "30px",
    "padding-bottom": "20px",
    "padding-top": "20px",
}


class OPTIONS(Enum):
    CALL = "Call"
    COVERED_CALL = "Covered Call"
    PUT = "Put"
    CASH_COVERED_PUT = "Cash Covered Put"


def get_price(ticker: str) -> float:
    headers = {"Content-Type": "application/json"}
    requestResponse = requests.get(
        f"""https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate=\
        {datetime.date.today()-datetime.timedelta(days=5)}&endDate=\
        {datetime.date.today()}&token={tiingo_api_key}&columns=close""",
        headers=headers,
    )
    # Getting most recent value, index 0
    most_recent_close_price = requestResponse.json()[0]["close"]
    return most_recent_close_price


def get_company_name(ticker: str) -> str:
    headers = {"Content-Type": "application/json"}
    requestResponse = requests.get(
        f"https://api.tiingo.com/tiingo/daily/{ticker}?token={tiingo_api_key}",
        headers=headers,
    )
    return requestResponse.json()["name"]


layout = {
    "paper_bgcolor": "#222",
    "plot_bgcolor": "#222",
    "titlefont": {"color": "#FFF"},
    "xaxis": {"tickfont": {"color": "#FFF"}},
    "yaxis": {"tickfont": {"color": "#FFF"}},
    "showlegend": True,
    "hovermode": "x unified",
    "font_color": "white",
    "hoverlabel": dict(
        font_size=16,
        font_family="Rockwell",
        font_color="white",
        bgcolor="black",
    ),
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

df = pd.DataFrame(data={"Stock Price": [1, 2], "Profit": [1, 2]})

fig = go.Figure(layout=layout)

y_axis_min = df["Profit"].min() - 1
if y_axis_min > 0:
    y_axis_min = -1

# Adds range and titles
fig.update_layout(
    xaxis_range=[df["Stock Price"].min(), df["Stock Price"].max()],
    yaxis_range=[y_axis_min, df["Profit"].max() + 1],
    xaxis_title="Stock Price",
    yaxis_title="Profit",
)

fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")
fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")


def html_div(
    label_name,
    default_val,
    val_type,
    id_val,
    pattern,
    step="any",
    style=DEFAULT_STYLE,
):
    return html.Div(
        [
            html.Label(label_name, id="label_" + id_val),
            dbc.Input(
                value=default_val,
                type=val_type,
                id="input_" + id_val,
                step=step,
                pattern=pattern,
            ),
        ],
        style=style,
    )


tabular_view = [
    dcc.Tab(
        label=l,
        value=l,
    )
    for l in [
        OPTIONS.CALL.value,
        OPTIONS.COVERED_CALL.value,
        OPTIONS.PUT.value,
        OPTIONS.CASH_COVERED_PUT.value,
    ]
]


app.layout = html.Div(
    [
        dcc.Tabs(
            id="input_option_type",
            value=OPTIONS.CALL.value,
            children=tabular_view,
            colors={
                "border": "black",
                "primary": "navy",
                "background": "black",
            },
        ),
        html.Div(
            id="content",
            children=[
                html_div(
                    id_val="ticker",
                    label_name="Stock Ticker",
                    default_val="",
                    val_type="text",
                    pattern="^[a-zA-Z]{0,4}",
                ),
                html_div(
                    id_val="price",
                    label_name="Price of stock",
                    default_val=0,
                    val_type="number",
                    step=0.01,
                    pattern=r"^[0-9]*\.?[0-9]+$",
                ),
                html_div(
                    id_val="average_price_paid",
                    label_name="Average Price Paid (Covered Calls only)",
                    default_val=0,
                    val_type="number",
                    pattern=r"^[0-9]*\.?[0-9]+$",
                ),
                html_div(
                    id_val="strike",
                    label_name="Get Strike",
                    default_val=0,
                    val_type="number",
                    step=0.5,
                    pattern=r"^[0-9]*\.?[0-9]+$",
                ),
                html_div(
                    id_val="premium",
                    label_name="Premium",
                    default_val=0,
                    val_type="number",
                    step=0.01,
                    pattern=r"^[0-9]*\.?[0-9]+$",
                ),
                html_div(
                    id_val="number_of_contracts",
                    label_name="#s of Contracts",
                    default_val=1,
                    val_type="number",
                    pattern="^[0-9]*$",
                ),
                html.Div(id="output_return"),
                html.Div(id="output_payoff"),
                html.Div(dcc.Graph(id="output_graph", figure=fig)),
                dash_table.DataTable(id="output_table"),
            ],
        ),
    ],
    className="dash-bootstrap",
)


@app.callback(
    Output("input_average_price_paid", "style"),
    Output("label_average_price_paid", "style"),
    Input("input_option_type", "value"),
)
def render_content(tab):
    if tab == "Covered Call":
        return DEFAULT_STYLE, {"display": "inline-block"}
    else:
        return {"display": "none"}, {"display": "none"}


@app.callback(
    Output(component_id="output_graph", component_property="figure"),
    Input(component_id="input_option_type", component_property="value"),
    Input(component_id="input_strike", component_property="value"),
    Input(component_id="input_premium", component_property="value"),
    Input(component_id="input_average_price_paid", component_property="value"),
    Input(component_id="input_price", component_property="value"),
    Input(component_id="input_number_of_contracts", component_property="value"),
)
def update_graph(
    input_option_type,
    input_strike,
    input_premium,
    input_average_price_paid,
    input_price,
    input_number_of_contracts,
):
    if input_number_of_contracts == None:
        input_number_of_contracts = 1
    stock_count = input_number_of_contracts * 100

    # Create dataframe and update the dataframe inputs using inputs
    fig = go.Figure(layout=layout)
    df = None
    if input_option_type == OPTIONS.CALL.value:
        df = return_call_array(input_strike, input_premium, stock_count)
    elif input_option_type == OPTIONS.PUT.value:
        df = return_put_array(input_strike, input_premium, stock_count)
    elif input_option_type == OPTIONS.COVERED_CALL.value:
        df = return_covered_call_array(
            input_strike,
            input_premium,
            stock_count,
            input_average_price_paid,
        )
    elif input_option_type == OPTIONS.CASH_COVERED_PUT.value:
        df = return_covered_cash_covered_put_array(
            input_strike, input_premium, stock_count
        )
    fig.add_trace(
        go.Scatter(
            x=df["Stock Price"], y=df["Profit"], name="Stock Price vs. Profit"
        )
    )

    fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")

    y_axis_min = df["Profit"].min() - 1

    if y_axis_min > 0:
        y_axis_min = -1

    # Adds range and titles
    fig.update_layout(
        xaxis_range=[df["Stock Price"].min(), df["Stock Price"].max()],
        yaxis_range=[y_axis_min, df["Profit"].max() + 1],
        xaxis_title="Stock Price",
        yaxis_title="Profit",
    )

    return fig


@app.callback(
    Output(component_id="input_price", component_property="value"),
    Output(component_id="input_strike", component_property="value"),
    Input(component_id="input_ticker", component_property="value"),
)
def update_price(input_ticker):
    layout["title"] = {"text": input_ticker}
    try:
        price = get_price(input_ticker)
        layout["title"] = {"text": get_company_name(input_ticker)}
    except:
        price = 0
    return price, math.ceil(price * 2) / 2


@app.callback(
    Output(component_id="output_table", component_property="data"),
    Input(component_id="input_option_type", component_property="value"),
    Input(component_id="input_strike", component_property="value"),
    Input(component_id="input_premium", component_property="value"),
    Input(component_id="input_average_price_paid", component_property="value"),
    Input(component_id="input_price", component_property="value"),
    Input(component_id="input_number_of_contracts", component_property="value"),
)
def update_table(
    input_option_type,
    input_strike,
    input_premium,
    input_average_price_paid,
    input_price,
    input_number_of_contracts,
):
    if input_number_of_contracts == None:
        input_number_of_contracts = 1
    if input_option_type == OPTIONS.CALL.value:
        df = return_call_array(
            input_strike, input_premium, input_number_of_contracts
        )
    elif input_option_type == OPTIONS.PUT.value:
        df = return_put_array(
            input_strike, input_premium, input_number_of_contracts
        )
    elif input_option_type == OPTIONS.COVERED_CALL.value:
        df = return_covered_call_array(
            input_strike,
            input_premium,
            input_number_of_contracts,
            input_average_price_paid,
        )
    elif input_option_type == OPTIONS.CASH_COVERED_PUT.value:
        df = return_covered_cash_covered_put_array(
            input_strike, input_premium, input_number_of_contracts
        )
    else:
        df = pd.DataFrame({"Price": []})

    return df.to_dict("records")


if __name__ == "__main__":
    app.run_server(debug=True)
