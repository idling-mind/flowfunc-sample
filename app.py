from pathlib import Path
import time
import flowfunc
from flowfunc.config import Config
from flowfunc.jobrunner import JobRunner
from flowfunc.models import OutNode
import dash
from dash.dependencies import Input, Output, State, ALL
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_resizable_panels import Panel, PanelGroup, PanelResizeHandle
import json
import base64

from nodes import all_functions, extra_nodes

app = dash.Dash(external_stylesheets=[dbc.themes.SLATE])
app.title = "Flowfunc Demo"

HELP = """
# Help
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


#### Help

Click the help button to see this help. If you select a node and click the button,
you will see the docstring of the function that the node represents.

"""

sample_flow_files = (Path(".") / "sample_flows").glob("**/*.json")
sample_flows = [
    dbc.DropdownMenuItem(x.stem, id={"type": "sampleflow", "file": x.name})
    for x in sample_flow_files
]

fconfig = Config.from_function_list(all_functions, extra_nodes=extra_nodes)
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
                dbc.Button(id="help", children="Help"),
                dash.dcc.Store(id="nodestore", storage_type="local"),
            ],
            style={
                "position": "absolute",
                "top": "15px",
                "left": "15px",
                "zIndex": "15",
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

horizontal_resizer = PanelResizeHandle(
    html.Div(
        style={
            "backgroundColor": "#333333",
            "height": "5px",
            "width": "100%",
        }
    )
)
vertical_resizer = PanelResizeHandle(
    html.Div(
        style={
            "backgroundColor": "#333333",
            "height": "100%",
            "width": "5px",
        }
    )
)

panel_style = {
    "maxHeight": "100%",
    "overflow": "auto",
    "padding": "15px",
}

app.layout = html.Div(
    [
        PanelGroup(
            id="panel-group",
            children=[
                Panel(
                    id="panel-1",
                    children=[node_editor],
                ),
                horizontal_resizer,
                Panel(
                    id="panel-2",
                    children=[
                        PanelGroup(
                            [
                                Panel(
                                    children=html.Div(
                                        [
                                            html.H1("Output"),
                                            dash.dcc.Loading(
                                                type="circle",
                                                children=html.Div(
                                                    "Run some flow to see it's output",
                                                    id="output",
                                                ),
                                            ),
                                        ],
                                        style=panel_style,
                                    )
                                ),
                                vertical_resizer,
                                Panel(
                                    children=html.Div(id="nodehelp", style=panel_style)
                                ),
                            ],
                            direction="horizontal",
                        ),
                    ],
                ),
            ],
            direction="vertical",
        )
    ],
    style={"height": "100vh"},
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
        return ["Run some flow to see it's output"], {}
    starttime = time.perf_counter()
    # output_dict = job_runner.run(nodes)
    nodes_output = job_runner.run(nodes)
    # nodes_output = {node_id: OutNode(**node) for node_id, node in output_dict.items()}
    endtime = time.perf_counter()
    children = []
    for node in nodes_output.values():
        if node.error:
            children.append(
                html.Div(
                    [
                        html.B(
                            f"Node {node.id} ({node.type}): {node.error.__class__.__name__}"
                        ),
                        html.P(str(node.error), style={"color": "#cc0000"}),
                    ]
                )
            )
        if "display" in node.type:
            children.append(html.Div(node.result))
    outdiv = html.Div(children=children)

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
    Output("nodehelp", "children"),
    Input("help", "n_clicks"),
    State("input", "selected_nodes"),
    State("input", "nodes"),
)
def func(nclicks, selected_node, nodes):
    if not selected_node:
        return dash.dcc.Markdown(HELP)
    outnode = OutNode(**nodes.get(selected_node[0]))
    node = fconfig.get_node(outnode.type)
    return html.Div(
        [
            html.H1(node.label),
            dash.html.Code(
                dash.html.Pre(node.method.__doc__, style={"fontSize": "1em"})
            ),
        ]
    )


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
    app.run_server(debug=True)
