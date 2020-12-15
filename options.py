import requests
import os
import datetime
import pandas as pd
import numpy as np
import decimal


tiingo_api_key = os.getenv('TIINGO_API_KEY')

def get_price_from_tiingo(ticker):
    headers = {
        'Content-Type': 'application/json'
    }
    requestResponse = requests.get(f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={datetime.date.today()-datetime.timedelta(days=5)}&endDate={datetime.date.today()}&token={tiingo_api_key}&columns=close", headers=headers)
    
    return requestResponse.json()[0]['close']


def float_range(stop, step):
    
    start = 0

    while start < stop:
        yield float(start)
        start += decimal.Decimal(step)

def intialize_df_x(strike_price):

    df= pd.DataFrame(columns=['x'],data=float_range(stop = strike_price*20 ,step =0.01))

    return df

def return_array(strike_price):
    
    df = intialize_df_x(strike_price)
    df['y'] = df['x'].apply(lambda x: x-strike_price if x>strike_price else 0)

    return df

def return_call_array(strike_price,premium):

    df = intialize_df_x(strike_price)
    df['y'] = df['x'].apply(lambda x: x-strike_price-premium if x>strike_price else 0-premium)

    return df

def return_covered_call_array(strike_price,premium,avg_price):

    df = intialize_df_x(strike_price)
    df['y'] = df['x'].apply(lambda x: strike_price-avg_price+premium if x>=strike_price else x-avg_price+premium)

    return df


def return_put_array(strike_price,premium):

    df= pd.DataFrame(columns=['x'],data=float_range(stop = strike_price*20 ,step =0.01))
    df['y'] = df['x'].apply(lambda x: strike_price-x-premium if x<strike_price else 0-premium)

    return df



import dash
import dash_core_components as dcc
import dash_html_components as html

import plotly.express as px
import plotly.graph_objects as go

from dash.dependencies import Input, Output



app = dash.Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

df = pd.DataFrame(data={'x': [1, 2], 'y': [1,2]})


fig = px.line(df, x="x", y="y")

fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')
fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')

app.layout = html.Div(children=[
    html.Label('Option Option'),
    dcc.Dropdown(id='option_option',
        options=[
            {'label': 'Call', 'value': 'call'},
            {'label': 'Covered Call', 'value': 'covered_call'},
            {'label': 'Put', 'value': 'put'},
            {'label': 'Cash Covered Put', 'value': 'cash_covered_put'}
        ],
        value='Call'
    ),

    html.Label('Get stock'),
    dcc.Input(value='TICKER', type='text',id='input_ticker'),

    html.Label('Price of stock'),
    dcc.Input(type='number',id='input_price',value = 0),

    html.Label('Avg Price paid (Covered Calls only)'),
    dcc.Input(type='number',id='input_avg_price'),

    html.Label('Strike'),
    dcc.Input(type='number',id='input_Strike'),
    html.Label('Premium'),
    dcc.Input(type='number',id='input_premium'),

    html.Button('Submit', id='button_submit'),
 

    dcc.Graph(
        id='Option_graph',
        figure=fig
    )
])

@app.callback(
    Output(component_id='Option_graph', component_property='figure'),
    Input(component_id='option_option', component_property='value'),
    Input(component_id='input_Strike', component_property='value'),
    Input(component_id='input_premium', component_property='value'),
    Input(component_id='input_avg_price', component_property='value'),
    Input(component_id='input_price', component_property='value')
    )
def update_graph(option_option,input_Strike,input_premium,input_avg_price,input_price):

    fig = go.Figure()

    df = pd.DataFrame(data={'x': [0,1, 2], 'y': [0,1,2]})

    if option_option == 'call':
        df = return_call_array(input_Strike,input_premium)
        fig.add_trace(go.Scatter(x=df["x"], y=df["y"], 
                                 text=f'$ {input_price}',name='Call'))


    elif option_option == 'put':
        df = return_put_array(input_Strike,input_premium)
        fig.add_trace(go.Scatter(x=df["x"], y=df["y"], name='Put'))

    elif option_option == 'covered_call':
        df = return_covered_call_array(input_Strike,input_premium,input_avg_price)
        fig.add_trace(go.Scatter(x=df["x"], y=df["y"], name='Covered Call'))

    fig.add_trace(go.Scatter(x=[input_price],y=df.loc[df['x']==input_price]['y'],
                             mode='markers',
                             marker = {'size':10},
                             text=f'$ {input_price}',name='You are here'))

    fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')

    y_axis_min = df['y'].min()-1

    if y_axis_min>0:
        y_axis_min=-1

    fig.update_layout(xaxis_range=[df['x'].min(),df['x'].max()],
                      yaxis_range=[y_axis_min,df['y'].max()+1])
    

    return fig

@app.callback(
    Output(component_id='input_price', component_property='value'),
    Input(component_id='input_ticker', component_property='value'),
    )
def update_graph(input_ticker):

    try:
        price = get_price_from_tiingo(input_ticker)
    
    except Exception as e:
        print(e)
        price = 0

    return price


if __name__ == '__main__':
    app.run_server(debug=True)