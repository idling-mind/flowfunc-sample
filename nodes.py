from functools import lru_cache
from enum import Enum
from typing import Any, Union, Tuple
from dash import html, dcc
import plotly.express as px
import pandas as pd
import numpy as np
import asyncio
import time
import dash


def dataframe_to_datatable(df: pd.DataFrame):
    """Convert dataframe to a dash datatable so that it can be displayed
    Parameters
    ----------
    df: dataframe
        Dataframe
    Returns
    -------
    Datatable : object
        Dash datatable
    """
    ddf = df.copy().reset_index()
    if isinstance(ddf.columns[0], tuple):
        ddf.columns = [
            ".".join(x) for x in df.columns.tolist()
        ]  # For multiindex columns
    from dash import dash_table

    return dash_table.DataTable(
        id="table",
        columns=[{"name": col, "id": col} for col in ddf.columns.tolist()],
        data=ddf.to_dict("records"),
    )


def markdown(markdown: str):
    """Display Markdown
    Display markdown in the dash app
    Parameters
    ----------
    markdown: str
        Markdown to display
    Returns
    -------
    markdown: object
        Dash markdown object
    """
    return dash.dcc.Markdown(markdown)


def display(output1, output2="", output3="", output4="", output5=""):
    """Display outputs"""
    outputs = []
    for output in [output1, output2, output3, output4, output5]:
        if isinstance(output, pd.DataFrame):
            outputs.append(dataframe_to_datatable(output))
        elif isinstance(output, dash.development.base_component.Component):
            outputs.append(output)
        else:
            try:
                outputs.append(str(output))
            except Exception as e:
                outputs.append(f"Error: {e}")
    return html.Div(outputs)


class DataFileType(Enum):
    csv = "csv"
    excel = "excel"


def read_dataframe(url: str, data_type: DataFileType, separator: str) -> pd.DataFrame:
    """Read a dataframe"""
    if data_type.value == "csv":
        return pd.read_csv(url, sep=separator)
    elif data_type.value == "excel":
        return pd.read_excel(url)
    return pd.read_table(url)


class SampleDataURL(Enum):
    iris = "https://gist.github.com/netj/8836201/raw/6f9306ad21398ea43cba4f7d537619d0e07d5ae3/iris.csv"
    titanic = "https://github.com/datasciencedojo/datasets/raw/master/titanic.csv"


@lru_cache(maxsize=None)
def sample_data(dataset: SampleDataURL) -> pd.DataFrame:
    """Sample data sets like tianic, iris etc"""
    return read_dataframe(dataset.value, DataFileType.csv, ",")


def scatter_plot(df: pd.DataFrame, x: str, y: str, color: str = "") -> dcc.Graph:
    """Create a scatter plot from a dataframe

    Parameters
    ----------
    df: DataFrame
        Dataframe to use for the plot
    x: str
        Name of the column to be as the x axis
    y: str
        Name of the column to be as the y axis
    color: str
        Name of the column to be used for color

    Returns
    -------
    dcc.Graph: A graph object that can be displayed in the dash app
    """
    return dcc.Graph(figure=px.scatter(df, x=x, y=y, color=color))


def bubble_plot(
    df: pd.DataFrame, x: str, y: str, size: str, color: str = ""
) -> dcc.Graph:
    """Create a bubble plot from a dataframe

    Parameters
    ----------
    df: DataFrame
        Dataframe to use for the plot
    x: str
        Name of the column to be as the x axis
    y: str
        Name of the column to be as the y axis
    size: str
        Name of the column to be as the size of each bubble
    color: str
        Name of the column to be used for color

    Returns
    -------
    dcc.Graph: A graph object that can be displayed in the dash app
    """
    return dcc.Graph(figure=px.scatter(df, x=x, y=y, size=size, color=color))


def scatter_plot_3d(
    df: pd.DataFrame, x: str, y: str, z: str, color: str = ""
) -> dcc.Graph:
    """Create a 3d scatter plot from a dataframe

    Parameters
    ----------
    df: DataFrame
        Dataframe to use for the plot
    x: str
        Name of the column to be as the x axis
    y: str
        Name of the column to be as the y axis
    z: str
        Name of the column to be as the z axis
    color: str
        Name of the column to be used for color

    Returns
    -------
    dcc.Graph: A graph object that can be displayed in the dash app
    """
    return dcc.Graph(figure=px.scatter_3d(df, x=x, y=y, z=z, color=color))


def bar_plot(df: pd.DataFrame, x: str, y: str, color: str = "") -> dcc.Graph:
    """Create a bar plot from a dataframe"""
    return dcc.Graph(figure=px.bar(df, x=x, y=y, color=color))


def describe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Statistics of a dataframe"""
    return df.describe()


all_functions = [
    markdown,
    display,
    scatter_plot,
    bubble_plot,
    bar_plot,
    scatter_plot_3d,
    sample_data,
    describe_dataframe,
]
