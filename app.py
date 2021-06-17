import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html 
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.express as px
import pandas as pd
import re

# Load data  --------------
## Load Excel data
url1 = 'https://sewerpollutants.s3.us-west-2.amazonaws.com/LIMS.xls'
df = pd.read_excel(url1,index_col=0, parse_dates=True)
## Load pollutant limits
url2 = 'https://sewerpollutants.s3.us-west-2.amazonaws.com/LocalLimits.csv'
pollutant_limit = pd.read_csv(url2)

# Format data  --------------
df["pollutant_abb"] = df.PARAMLISTDESC.apply(lambda x: re.sub(" *\-.+", "", x)) # remove -Total Recoverable
df.sort_values("pollutant_abb", inplace = True)

df = pd.merge(df, pollutant_limit, left_on = "pollutant_abb", right_on = "Metal", how = "inner")

## New column with company ids
df["company_id"] = df.SAMPLEDESC.apply(lambda x: re.sub("Site Code ", "", x)) # remove -Total Recoverable
df["company_id"] = df["company_id"].astype(int)

# Convert display value column to numeric
df.DISPLAYVALUE = df.DISPLAYVALUE.apply(lambda x: re.sub(">|<", "", x))
df.DISPLAYVALUE = pd.to_numeric(df.DISPLAYVALUE, errors = "coerce")

#%% Dash layout

external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
server = app.server

app.layout = html.Div([
	html.Center(html.H2("Sewer Pollutants")),
	html.Center(html.H6("Interactive Dashboard using Laboratory Information Management System(LIMS) data")),
	html.Div(dcc.Tabs([
        ################## TAB A ###################
		dcc.Tab([
			html.Div([
				dcc.Dropdown(id='pollutant-dropdown', 
					options = [{'label': str(pltn), 'value': str(pltn)} for pltn in df.pollutant_abb.unique()], 
					multi = True, className = "ml-3 mr-3 mt-2", placeholder = "Select pollutant(s)"),
				html.Div(dcc.Loading(id = 'barchart'))  # or dbc.Spinner
			]) # html.div
		], label = "EPA metal Pollutants of Concern (POC)"), # dbc.Col dcc.Tab
        ################## TAB B ###################
		dcc.Tab([
			html.Div([
                #--------------- ROW 1-----------------------------
				dcc.Dropdown(id='company-dropdown-B', 
					options = [{'label': str(comp), 'value': str(comp)} for comp in df.sort_values("company_id").SAMPLEDESC.unique()], 
					multi = False, value = "Site Code 1", placeholder = "Select company", className = "ml-3 mr-3 mt-2 mb-2"),
                #--------------- ROW 2 (Company stats) -------------------------
                html.Br(),
                dbc.Row(html.H4("Percentage of times exceeded"), className = "ml-5", justify = "center"),
                html.Br(),
                dbc.Row(id = "pollutants-gauge-row-B"),
                dbc.Row([dbc.Button("All pollutants (Expand)", id = "collapse-button-B", color = "primary", className = "mb-3 mt-3 ml-5", )]),
                dbc.Collapse(dbc.Row(id = "collapse-row-B"), id = "collapse-B"),
			]) # html.div
		], label = "Pollutants exceeding limit by Company") # dbc.Col dcc.Tab 
        ################## END OF TABS ###################
	]))
])


#%% Callbacks
####### TAB 1 ##############
@app.callback(
	Output("barchart", "children"),
	[Input("pollutant-dropdown", "value")]
)
def filterPollutants(selected_pollutants):
	if selected_pollutants:
		dff = df.loc[df.pollutant_abb.isin(selected_pollutants)]
	else:
		dff = df
	
	bar_fig = {'data':[
			go.Bar(
			x = dff['U_SAMPLE_DTTM'],
			y = dff['DISPLAYVALUE'],
			)], 
	'layout':go.Layout(title='Sampling for Local Limits',
			# yaxis_range=[0,2],
			yaxis_title_text='Metals mg/L'
			)}		

	# line_fig = px.line(dff, x= "U_SAMPLE_DTTM", y = "DISPLAYVALUE", color = "pollutant_abb",#  template = "simple_white",
	# 	title = "Sampling for Local Limits")

	# line_fig.update_layout({"yaxis": {"title": {"text": "Metals mg/L"}}})
			
	return dcc.Graph(figure = bar_fig)

####### TAB 2 ##############
@app.callback(
	[Output("pollutants-gauge-row-B", "children"), Output("collapse-row-B", "children")],
	Input("company-dropdown-B", "value")
)
def filterCompanyB(selected_company):
    if selected_company:
        dff = df.loc[df.SAMPLEDESC.isin([selected_company])]
        dff["exceeds_limits"] = dff.apply(lambda row: row.DISPLAYVALUE > row.Limit, axis = 1)
        ## Order pollutants in descending order (% of timepoints exceeding limit)
        dff_aux = dff.groupby("pollutant_abb").exceeds_limits.mean().reset_index()
        pollutant_list = dff_aux.sort_values("exceeds_limits", ascending = False).pollutant_abb
        
        POLLUTANT_STATS = [] # Container that will hold the gauge Divs
        POLLUTANT_COLLAPSE = [] # Container that will hold the gauge Divs in excess of the top 6
        
        for pollutant in pollutant_list:
            dff_filt = dff.loc[dff.pollutant_abb == pollutant]
            pctg_exceeded = dff_filt.exceeds_limits.mean() * 100
            
            if len(POLLUTANT_STATS) < 8:
                POLLUTANT_STATS.append(
                    dbc.Col([
                        dbc.Row([html.H6(pollutant)], justify = "center"),
                        dbc.Row([
                            daq.Gauge(value = pctg_exceeded, min = 0, max = 100, size = 170, 
                                           label = str(int(pctg_exceeded)) + "%",  labelPosition = "bottom",
                                           className = "ml-3 mr-3")
                        ], justify = "center")
                    ], width = 3) # 2nd Row (Gauge)
                )
                
            else:
                POLLUTANT_COLLAPSE.append(
                    dbc.Col([
                        dbc.Row([html.H6(pollutant)], justify = "center"),
                        dbc.Row([
                            daq.Gauge(value = pctg_exceeded, min = 0, max = 100, size = 170, 
                                           label = str(int(pctg_exceeded)) + "%",  labelPosition = "bottom",
                                           className = "ml-3 mr-3")
                        ], justify = "center")
                    ], width = 3) # 2nd Row (Gauge)
                )
            
        return POLLUTANT_STATS, POLLUTANT_COLLAPSE
        
# Collapse button functionality
@app.callback(Output("collapse-B", "is_open"),
              [Input("collapse-button-B", "n_clicks")],
              [State("collapse-B", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


#%%
if __name__ == "__main__":
        app.run_server(debug=True)