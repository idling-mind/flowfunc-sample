from pathlib import Path
import time
import flowfunc
from flowfunc.config import Config
from flowfunc.jobrunner import JobRunner
import dash
from dash.dependencies import Input, Output, State, ALL
from dash import html, dcc
import dash_bootstrap_components as dbc
import json
import base64

from flowfunc.models import OutNode
from nodes import all_functions

app = dash.Dash(external_stylesheets=[dbc.themes.SLATE])
app.title = "Flowfunc Demo"

HELP = """
This is an example usage of [Dash Flowfunc Component](https://github.com/idling-mind/flowfunc).
You can find the source code for this example [here](https://github.com/idling-mind/flowfunc-sample)

## How to use this example

As a start, try one of the sample flows provided by clicking one from the
dropdown.

Once you're familar, try adding new nodes by right cliking on the node editor
and select a node to be added to the editor.
For eg: Add the `Sample Data` node. Now add another node called `Display`.
Now you can connect the output node of `Sample Data` to the first input node
of the `Display` node and click the `Run` button. This will evaluate both the 
nodes and will display the output in the output section.

## The different buttons

#### Run

Click the `Run` button to evaluate the current nodes

#### Save

If you click the `Save` button, the nodes are saved to the browser memory using `dash.dcc.Store`.

#### Restore

When you click the `Restore` button, the data in the store is retrieved and is set as the nodes of
the node editor. 

#### Download

You can download the nodes as a json file if you click the download button.

#### Clear

Clear the editor

#### Load

Load a previously downloaded node file

#### Sample flows

Some sample flows for you to start with.


## Help for each node

Click any node to see a help on that node in this sidebar
"""

sample_flow_files = (Path(".") / "sample_flows").glob("**/*.json")
sample_flows = [
    dbc.DropdownMenuItem(x.stem, id={"type": "sampleflow", "file": x.name})
    for x in sample_flow_files
]

fconfig = Config.from_function_list(all_functions)
job_runner = JobRunner(fconfig)

node_editor = html.Div(
    [
        dbc.ButtonGroup(
            [
                dbc.Button(id="run", children="Run"),
                dbc.Button(id="save", children="Save"),
                dbc.Button(id="restore", children="Restore"),
                dbc.Button(id="download", children="Download"),
                dbc.Button(id="clear", children="Clear"),
                dcc.Upload(
                    id="uploader", children=dbc.Button(id="load", children="Load")
                ),
                dash.dcc.Download(id="nodedownload"),
                dbc.DropdownMenu(
                    sample_flows,
                    label="Sample Flows",
                    group=True,
                ),
                dash.dcc.Store(id="nodestore", storage_type="local"),
            ],
            style={
                "position": "absolute",
                "top": "15px",
                "left": "15px",
                "z-index": "15",
            },
        ),
        html.Div(
            id="nodeeditor_container",
            children=flowfunc.Flowfunc(
                id="input",
                config=fconfig.dict(),
                # default_nodes=[{"type": "nodes.display", "x": 0, "y": 0}],
                context={"context": "initial"},
            ),
            style={
                "position": "relative",
                "width": "100%",
                "height": "100vh",
            },
        ),
    ]
)

app.layout = html.Div(
    dbc.Row(
        [
            dbc.Col(width=8, children=node_editor, style={"padding": 0}),
            dbc.Col(
                id="output_col",
                width=4,
                style={"height": "100vh", "overflow": "auto", "padding": 0},
                children=[
                    dbc.Accordion(
                        [
                            dbc.AccordionItem(
                                [dash.dcc.Markdown(HELP)],
                                title="Help",
                            ),
                            dbc.AccordionItem(
                                id="nodehelp",
                                title="Node Help",
                            ),
                            dbc.AccordionItem(
                                [
                                    html.Div(
                                        children=dash.dcc.Loading(
                                            id="loading_comp",
                                            type="circle",
                                            children=html.Div(id="output"),
                                        ),
                                    ),
                                ],
                                title="Output",
                            ),
                        ],
                        flush=True,
                        start_collapsed=True,
                    )
                ],
            ),
        ],
    ),
    style={"overflow": "hidden"},
)


def parse_uploaded_contents(contents):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    data = json.loads(decoded.decode("utf-8"))
    try:
        for key, value in data.items():
            node = OutNode(**value)
        # Parsing succeeded
        return data
    except Exception as e:
        print(e)
        print("The uploaded file could not be parsed as a flow file.")


@app.callback(
    [
        Output("output", "children"),
        Output("input", "nodes_status"),
    ],
    [
        Input("run", "n_clicks"),
        State("input", "nodes"),
    ],
)
def display_output(runclicks, nodes):
    if not nodes:
        return [], {}
    starttime = time.perf_counter()
    # output_dict = job_runner.run(nodes)
    nodes_output = job_runner.run(nodes)
    # nodes_output = {node_id: OutNode(**node) for node_id, node in output_dict.items()}
    endtime = time.perf_counter()
    outdiv = html.Div(children=[])
    for node in nodes_output.values():
        if node.error:
            outdiv.children.append(str(node.error))
        if "display" in node.type:
            outdiv.children.append(node.result)

    return outdiv, {node_id: node.status for node_id, node in nodes_output.items()}


@app.callback(
    Output("nodedownload", "data"),
    [Input("download", "n_clicks"), State("input", "nodes")],
    prevent_initial_call=True,
)
def func(n_clicks, nodes):
    return dict(content=json.dumps(nodes), filename="nodes.json")


@app.callback(
    Output("nodestore", "data"),
    [Input("save", "n_clicks"), State("input", "nodes")],
    prevent_initial_call=True,
)
def func(n_clicks, nodes):
    return nodes


@app.callback(
    [
        Output("nodehelp", "title"),
        Output("nodehelp", "children"),
    ],
    [
        Input("input", "selected_nodes"),
        State("input", "nodes"),
    ],
)
def func(selected_node, nodes):
    if not selected_node:
        return "Node Help", "Click a node to see it's help"
    outnode = OutNode(**nodes.get(selected_node[0]))
    node = fconfig.get_node(outnode.type)
    return f"Help for {node.label}", dash.html.Code(dash.html.Pre(node.method.__doc__))


@app.callback(
    [
        Output("input", "nodes"),
        Output("input", "editor_status"),
    ],
    [
        Input("uploader", "contents"),
        Input("clear", "n_clicks"),
        Input("restore", "n_clicks"),
        Input({"type": "sampleflow", "file": ALL}, "n_clicks"),
        State("input", "nodes"),
        State("nodestore", "data"),
    ],
    prevent_initial_call=True,
)
def update_output(
    contents, nclicks, restore_clicks, sample_flow_button, nodes, storenodes
):
    ctx = dash.callback_context
    if not ctx.triggered:
        return nodes, "server"
    control = ctx.triggered[0]["prop_id"].split(".")[0]
    if control == "uploader":
        newnodes = parse_uploaded_contents(contents)
        return newnodes, "server"
    if control == "restore":
        return storenodes, "server"
    elif (
        isinstance(ctx.triggered_id, dict)
        and ctx.triggered_id.get("type") == "sampleflow"
    ):
        newnodes_json = (
            Path(".") / "sample_flows" / ctx.triggered_id["file"]
        ).read_text()
        newnodes = json.loads(newnodes_json)
        return newnodes, "server"
    return {}, "server"


if __name__ == "__main__":
    app.run_server()
