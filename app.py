import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html 
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import re

# Load data

url1 = 'https://sewerpollutants.s3.us-west-2.amazonaws.com/LIMS.xls'
df = pd.read_excel(url1,index_col=0, parse_dates=True)
df["pollutant_abb"] = df.PARAMLISTDESC.apply(lambda x: re.sub(" *\-.+", "", x)) # remove -Total Recoverable
df.sort_values("pollutant_abb", inplace = True)


# Plot data

external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
server = app.server   # for Heroku Pipelines

app.layout = html.Div([
	html.Center(html.H2("Sewer Pollutants")),
	html.Center(html.H6("Interactive Dashboard using Laboratory Information Management System(LIMS) data")),
	html.Div(dcc.Tabs([
		dcc.Tab([
			html.Div([
				dcc.Dropdown(id='pollutant-dropdown', 
					options = [{'label': str(pltn), 'value': str(pltn)} for pltn in df.pollutant_abb.unique()], 
					multi = True, className = "ml-3 mr-3"),
				html.Div(dcc.Loading(id = 'barchart'))  # or dbc.Spinner
			]) # html.div
		], label = "EPA metal Pollutants of Concern (POC)") # dbc.Col dcc.Tab
	]))
])


# Callbacks

@app.callback(
	Output("barchart", "children"),
	Input("pollutant-dropdown", "value")
)
def filterPollutants(selected_pollutants):
	if selected_pollutants:
		dff = df.loc[df.pollutant_abb.isin(selected_pollutants)]
	else:
		dff = df
	
	# bar_fig = {'data':[
	# 		go.Bar(
	# 		x = dff['U_SAMPLE_DTTM'],
	# 		y = dff['DISPLAYVALUE'],
	# 		)], 
	# 'layout':go.Layout(title='Sampling for Local Limits',
	# 		# yaxis_range=[0,2],
	# 		yaxis_title_text='Metals mg/L'
	# 		)}		

	line_fig = px.line(dff, x= "U_SAMPLE_DTTM", y = "DISPLAYVALUE", color = "pollutant_abb", template = "simple_white",
		title = "Sampling for Local Limits")

	line_fig.update_layout({"yaxis": {"title": {"text": "Metals mg/L"}}})

	return dcc.Graph(figure = line_fig)



if __name__ == "__main__":
        app.run_server(debug=True)