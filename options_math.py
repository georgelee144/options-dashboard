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


def return_call_array(strike_price, premium, number_of_contracts):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: max(x - strike_price, 0) - premium
    )
    df["Total Profit"] = df["Profit"] * number_of_contracts

    df["Return"] = df["Profit"] / premium

    return df


def return_covered_call_array(
    strike_price, premium, number_of_contracts, avg_price
):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: max(strike_price, x) - avg_price + premium
    )
    df["Total Profit"] = df["Profit"] * number_of_contracts

    df["Return"] = df["Profit"] / (avg_price + strike_price)

    return df


def return_put_array(strike_price, premium, number_of_contracts):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: max(strike_price - x, 0) - premium
    )

    df["Total Profit"] = df["Profit"] * number_of_contracts

    df["Return"] = df["Profit"] / (strike_price)

    return df


def return_covered_cash_covered_put_array(
    strike_price, premium, number_of_contracts
):

    df = intialize_df_x(strike_price)
    df["Profit"] = df["Stock Price"].apply(
        lambda x: max(strike_price - x, 0) - premium
    )

    df["Total Profit"] = df["Profit"] * number_of_contracts

    return df