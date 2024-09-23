from functools import lru_cache
from enum import Enum
from tokenize import group
from typing import Any, List, Union, Tuple
from dash import html, dcc
from dash import dash_table
import plotly.express as px
import pandas as pd
import numpy as np
import asyncio
import time
import dash
from flowfunc.models import Port, Node, PortFunction


def display_function(**kwargs):
    """Display the output of the flow"""
    outputs = []
    for output in kwargs.values():
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


display_node = Node(
    type="display",
    label="Display Outputs",
    description="Display the output of the flow",
    method=display_function,
    inputs=PortFunction(path="increasing_ports"),
)


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
    ddf = flatten_index(df)

    return dash_table.DataTable(
        id="table",
        columns=[{"name": col, "id": col} for col in ddf.columns.tolist()],
        data=ddf.to_dict("records"),
    )


def flatten_index(df):
    """Flatten the index of a multiindex dataframe"""
    ddf = df.copy()
    if any([isinstance(x, tuple) for x in ddf.columns]):
        ddf.columns = [
            ".".join(x) for x in df.columns.tolist()
        ]  # For multiindex columns

    ddf = ddf.reset_index()
    return ddf


def markdown(template: str, **kwargs):
    """Display Markdown

    Display markdown in the dash app. You can write any variable between curly braces
    and it will be replaced by the value of the variable. A port will be created for
    each variable

    Parameters
    ----------
    markdown: str
        Markdown to display
    Returns
    -------
    markdown: object
        Dash markdown object
    """
    return dash.dcc.Markdown(template.format(**kwargs))


markdown_node = Node(
    type="markdown",
    label="Markdown",
    description="Display markdown in the dash app",
    method=markdown,
    inputs=PortFunction(path="dynamic_ports"),
    outputs=[Port(type="str", name="markdown", label="Markdown")],
)


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
    countries = "https://github.com/bnokoro/Data-Science/raw/master/countries%20of%20the%20world.csv"


def sample_data(dataset: SampleDataURL) -> pd.DataFrame:
    """Sample data sets like tianic, iris etc"""
    return read_dataframe(dataset.value, DataFileType.csv, ",").dropna()


def filter_columns(df: pd.DataFrame, columns: str) -> pd.DataFrame:
    """Filter columns of a dataframe. Enter the column names as a comma separated string"""
    return df[[x.strip() for x in columns.split(",")]]


class Aggregations(Enum):
    """Dataframe aggregation methods"""

    min = "min"
    max = "max"
    mean = "mean"
    sum = "sum"


def group_and_aggregate(
    df: pd.DataFrame, groupby: str, aggregations: list[Aggregations]
) -> pd.DataFrame:
    """Groupby and aggregate a dataframe.

    In the groupby field, enter the names of the columns (comma separated) by
    which the groupby should be done. Also select the aggregation methods.
    """
    ret = df.groupby(
        [x.strip() for x in groupby.split(",")],
    ).agg([x.value for x in aggregations])
    ret = flatten_index(ret)
    return ret


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
    return dcc.Graph(figure=px.scatter(df.reset_index(), x=x, y=y, color=color))


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
    return dcc.Graph(
        figure=px.scatter(df.reset_index(), x=x, y=y, size=size, color=color)
    )


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
    return dcc.Graph(figure=px.scatter_3d(df.reset_index(), x=x, y=y, z=z, color=color))


def bar_plot(df: pd.DataFrame, x: str, y: str, color: str = "") -> dcc.Graph:
    """Create a bar plot from a dataframe"""
    return dcc.Graph(figure=px.bar(df.reset_index(), x=x, y=y, color=color))


def describe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Statistics of a dataframe"""
    return df.describe()

def aggregate_series(df: pd.DataFrame, name: str, agg: Aggregations):
    """Returns the aggregated value of a series"""
    return df.loc[:, name].agg(agg.value)


all_functions = [
    sample_data,
    filter_columns,
    group_and_aggregate,
    aggregate_series,
    scatter_plot,
    bubble_plot,
    bar_plot,
    scatter_plot_3d,
    describe_dataframe,
]

extra_nodes = [display_node, markdown_node]