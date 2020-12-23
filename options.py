import datetime
import decimal
import os
from enum import Enum, auto

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
from dash.dependencies import Input, Output
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


class OPTIONS(Enum):
    CALL = auto()
    COVERED_CALL = auto()
    PUT = auto()
    CASH_COVERED_PUT = auto()


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


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

fig = go.Figure(
    go.Indicator(
        mode="gauge+number+delta",
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "shape": "bullet",
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "darkblue",
            },
            "bgcolor": "black",
            "bordercolor": "white",
            "steps": [
                {"range": [0, 50], "color": "#B22222"},
                {"range": [50, 100], "color": "#006400"},
            ],
        },
    )
)


def html_div(
    label_name,
    default_val,
    val_type,
    id,
    pattern,
    step="any",
    style={
        "display": "inline-block",
        "flex-wrap": "wrap",
        "padding-right": "30px",
        "padding-bottom": "20px",
        "padding-top": "20px",
    },
):
    return html.Div(
        [
            html.Label(label_name),
            dbc.Input(
                value=default_val,
                type=val_type,
                id=id,
                step=step,
                pattern=pattern,
            ),
        ],
        style=style,
    )


app.layout = html.Div(
    children=[
        html.Label("Option Option"),
        dcc.Dropdown(
            id="input_option_type",
            options=[
                {"label": "Call", "value": OPTIONS.CALL.value},
                {"label": "Covered Call", "value": OPTIONS.COVERED_CALL.value},
                {"label": "Put", "value": OPTIONS.PUT.value},
                {
                    "label": "Cash Covered Put",
                    "value": OPTIONS.CASH_COVERED_PUT.value,
                },
            ],
            value=OPTIONS.CALL.value,
        ),
        html_div(
            id="input_ticker",
            label_name="Stock Ticker",
            default_val="",
            val_type="text",
            pattern="^[a-zA-Z]{0,4}",
        ),
        html_div(
            id="input_price",
            label_name="Price of stock",
            default_val=0,
            val_type="number",
            step=0.01,
            pattern="^[0-9]*\.?[0-9]+$",
        ),
        html_div(
            id="input_average_price_paid",
            label_name="Average Price Paid (Covered Calls only)",
            default_val=0,
            val_type="number",
            pattern="^[0-9]*\.?[0-9]+$",
        ),
        html_div(
            id="input_strike",
            label_name="Get Strike",
            default_val=0,
            val_type="number",
            step=0.5,
            pattern="^[0-9]*\.?[0-9]+$",
        ),
        html_div(
            id="input_premium",
            label_name="Premium",
            default_val=0,
            val_type="number",
            step=0.01,
            pattern="^[0-9]*\.?[0-9]+$",
        ),
        html_div(
            id="input_number_of_contracts",
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
    className="dash-bootstrap",
)

layout = {}


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

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "shape": "bullet",
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "darkblue",
                },
                "bgcolor": "black",
                "bordercolor": "white",
                "steps": [
                    {"range": [0, 50], "color": "#B22222"},
                    {"range": [50, 100], "color": "#006400"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 2},
                    "thickness": 0.75,
                    "value": input_price,
                },
            },
        )
    )

    return fig


@app.callback(
    Output(component_id="input_price", component_property="value"),
    Input(component_id="input_ticker", component_property="value"),
)
def update_price(input_ticker):
    layout["title"] = {"text": input_ticker}
    try:
        price = get_price(input_ticker)
        layout["title"] = {"text": get_company_name(input_ticker)}
    except:
        price = 0
    return price


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
