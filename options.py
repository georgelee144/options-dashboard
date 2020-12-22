import requests
import os
import datetime
import pandas as pd
import numpy as np
import decimal

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import plotly.express as px
import plotly.graph_objects as go

from dash.dependencies import Input, Output

tiingo_api_key = os.getenv("TIINGO_API_KEY")


def get_price_from_tiingo(ticker):
    headers = {"Content-Type": "application/json"}
    requestResponse = requests.get(
        f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={datetime.date.today()-datetime.timedelta(days=5)}&endDate={datetime.date.today()}&token={tiingo_api_key}&columns=close",
        headers=headers,
    )

    return requestResponse.json()[0]["close"]


def float_range(stop, step):

    start = 0

    while start < stop:
        yield float(start)
        start += decimal.Decimal(step)


def intialize_df_x(strike_price):

    df = pd.DataFrame(
        columns=["x"], data=float_range(stop=strike_price + 20, step=0.01)
    )

    return df


def return_array(strike_price):

    df = intialize_df_x(strike_price)
    df["y"] = df["x"].apply(lambda x: x - strike_price if x > strike_price else 0)

    return df


def return_call_array(strike_price, premium):

    df = intialize_df_x(strike_price)
    df["y"] = df["x"].apply(
        lambda x: x - strike_price - premium if x > strike_price else 0 - premium
    )

    return df


def return_covered_call_array(strike_price, premium, avg_price):

    df = intialize_df_x(strike_price)
    df["y"] = df["x"].apply(
        lambda x: strike_price - avg_price + premium
        if x >= strike_price
        else x - avg_price + premium
    )

    return df


def return_put_array(strike_price, premium):

    df = intialize_df_x(strike_price)
    df["y"] = df["x"].apply(
        lambda x: strike_price - x - premium if x < strike_price else 0 - premium
    )

    return df


def return_covered_cash_covered_put_array(strike_price, premium):

    df = intialize_df_x(strike_price)
    df["y"] = df["x"].apply(
        lambda x: strike_price - x - premium if x < strike_price else 0 - premium
    )

    return df


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

df = pd.DataFrame(data={"x": [1, 2], "y": [1, 2]})

fig = px.line(df, x="x", y="y")

fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")
fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")


def html_div(
    label_name,
    default_val,
    val_type,
    id,
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
            ),
        ],
        style=style,
    )


app.layout = html.Div(
    children=[
        html.Label("Option Option"),
        dcc.Dropdown(
            id="option_option",
            options=[
                {"label": "Call", "value": "call"},
                {"label": "Covered Call", "value": "covered_call"},
                {"label": "Put", "value": "put"},
                {"label": "Cash Covered Put", "value": "cash_covered_put"},
            ],
            value="Call",
        ),
        html_div(
            id="input_ticker",
            label_name="Get Stock",
            default_val="TICKER",
            val_type="text",
        ),
        html_div(
            id="input_price",
            label_name="Price of stock",
            default_val=0,
            val_type="number",
            step=0.01,
        ),
        html_div(
            id="input_avg_price",
            label_name="Avg Price paid (Covered Calls only)",
            default_val=0,
            val_type="number",
        ),
        html_div(
            id="input_Strike",
            label_name="Get Strike",
            default_val=0,
            val_type="number",
            step=0.5,
        ),
        html_div(
            id="input_premium",
            label_name="Premium",
            default_val=0,
            val_type="number",
            step=0.01,
        ),
        html_div(
            id="input_number_of_contracts",
            label_name="# of contracts",
            default_val=0,
            val_type="number",
        ),
        html.Div(id="output_return"),
        html.Div(id="output_payoff"),
        dcc.Graph(id="Option_graph", figure=fig),
        dash_table.DataTable(
            id="table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
        ),
    ],
    className="dash-bootstrap",
)

layout = {
    "paper_bgcolor": "#222",
    "plot_bgcolor": "#222",
    "titlefont": {"color": "#FFF"},
    "xaxis": {"tickfont": {"color": "#FFF"}},
    "yaxis": {"tickfont": {"color": "#FFF"}},
}

@app.callback(
    Output(component_id="Option_graph", component_property="figure"),
    Input(component_id="option_option", component_property="value"),
    Input(component_id="input_Strike", component_property="value"),
    Input(component_id="input_premium", component_property="value"),
    Input(component_id="input_avg_price", component_property="value"),
    Input(component_id="input_price", component_property="value"),
)
def update_graph(
    option_option, input_Strike, input_premium, input_avg_price, input_price
):

    fig = go.Figure(layout=layout)

    if option_option == "call":
        df = return_call_array(input_Strike, input_premium)
        fig.add_trace(
            go.Scatter(x=df["x"], y=df["y"], text=f"$ {input_price}", name="Call")
        )

    elif option_option == "put":
        df = return_put_array(input_Strike, input_premium)
        fig.add_trace(
            go.Scatter(x=df["x"], y=df["y"], text=f"$ {input_price}", name="Put")
        )

    elif option_option == "covered_call":
        df = return_covered_call_array(input_Strike, input_premium, input_avg_price)
        fig.add_trace(
            go.Scatter(
                x=df["x"], y=df["y"], text=f"$ {input_price}", name="Covered Call"
            )
        )

    elif option_option == "cash_covered_put":
        df = return_covered_cash_covered_put_array(input_Strike, input_premium)
        fig.add_trace(
            go.Scatter(
                x=df["x"], y=df["y"], text=f"$ {input_price}", name="Cash Covered Put"
            )
        )

    else:

        df = pd.DataFrame(data={"x": [0, 1, 2], "y": [0, 1, 2]})

    fig.add_trace(
        go.Scatter(
            x=[input_price],
            y=df.loc[df["x"] == input_price]["y"],
            mode="markers",
            marker={"size": 10},
            text=f"$ {input_price}",
            name="You are here",
        )
    )

    fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")

    y_axis_min = df["y"].min() - 1

    if y_axis_min > 0:
        y_axis_min = -1

    fig.update_layout(
        xaxis_range=[df["x"].min(), df["x"].max()],
        yaxis_range=[y_axis_min, df["y"].max() + 1],
    )

    return fig


@app.callback(
    Output(component_id="input_price", component_property="value"),
    Input(component_id="input_ticker", component_property="value"),
)
def get_price(input_ticker):

    try:
        price = get_price_from_tiingo(input_ticker)

    except Exception as e:
        print(e)
        price = 0

    return price


@app.callback(
    Output(component_id="table", component_property="data"),
    Input(component_id="option_option", component_property="value"),
    Input(component_id="input_Strike", component_property="value"),
    Input(component_id="input_premium", component_property="value"),
    Input(component_id="input_avg_price", component_property="value"),
    Input(component_id="input_price", component_property="value"),
)
def update_table(
    option_option, input_Strike, input_premium, input_avg_price, input_price
):
    pass
    return None


if __name__ == "__main__":
    app.run_server(debug=True)