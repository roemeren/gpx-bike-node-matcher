import dash
from dash import html, dcc, Input, Output

app = dash.Dash()

app.layout = html.Div([
    html.H1(children="🔊 SHOUT-O-MATIC v1.0"),
    dcc.Input(id="txt-type", value="type here"),
    html.Div(id="txt-caps", style={"marginTop": 20, "fontSize": 30}),
    html.Img(src="assets/shout.png", style={"height": "120px"}),
])

@app.callback(
    Output("txt-caps", "children"),
    Input("txt-type", "value")
)
def update(txt):
    return (
        txt if txt else "give me something to yell about"
    ).upper() + "!!!"

if __name__ == '__main__':
    app.run(port=8051)
