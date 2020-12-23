import pandas as pd
import decimal

def float_range(stop, step):

    start = 0

    while start < stop:
        yield float(start)
        start += decimal.Decimal(step)


def intialize_df_x(strike_price):

    df = pd.DataFrame(
        columns=["Stock Price"],
        data=float_range(stop=strike_price + 20, step=0.01),
    )

    return df


def return_array(strike_price):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: x - strike_price if x > strike_price else 0
    )

    return df


def return_total_profit(df, number_of_contracts):

    df["Total Profit"] = df["Profit"] * number_of_contracts

    return df


def return_call_array(strike_price, premium, number_of_contracts):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: x - strike_price - premium
        if x > strike_price
        else 0 - premium
    )
    df = return_total_profit(df, number_of_contracts)

    df['Return'] = df["Profit"]/premium

    return df


def return_covered_call_array(
    strike_price, premium, number_of_contracts, avg_price
):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: strike_price - avg_price + premium
        if x >= strike_price
        else x - avg_price + premium
    )
    df = return_total_profit(df, number_of_contracts)

    df['Return'] = df["Profit"]/(avg_price+strike_price)

    return df


def return_put_array(strike_price, premium, number_of_contracts):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: strike_price - x - premium
        if x < strike_price
        else 0 - premium
    )

    df = return_total_profit(df, number_of_contracts)

    df['Return'] = df["Profit"]/(strike_price)

    return df


def return_covered_cash_covered_put_array(
    strike_price, premium, number_of_contracts
):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: strike_price - x - premium
        if x < strike_price
        else 0 - premium
    )

    df = return_total_profit(df, number_of_contracts)

    return df