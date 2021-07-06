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
from datetime import datetime, timedelta

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

# Convert datetime into date
df["U_SAMPLE_DTTM"] = df["U_SAMPLE_DTTM"].apply(lambda x: x.date())

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
					multi = False, value = "Site Code 26", placeholder = "Select company", className = "ml-3 mr-3 mt-2 mb-2"),
                #--------------- ROW 2 (Company stats) -------------------------
                html.Br(),
                dbc.Row(html.H4("Percentage of times exceeded"), className = "ml-5", justify = "center"),
                html.Br(),
                dbc.Row(id = "pollutants-gauge-row-B"),
                dbc.Row([dbc.Button("All pollutants (Expand)", id = "collapse-button-B", color = "primary", className = "mb-3 mt-3 ml-5", )]),
                dbc.Collapse(dbc.Row(id = "collapse-row-B"), id = "collapse-B"),
                #--------------- ROW 3 (Company stats) -------------------------
                html.Hr(),
                dbc.Row([html.H4("Select pollutant", className = "mb-0"), 
                         dbc.Button(id = "site-code-lbl-B", outline = True, color = "secondary", className = "ml-3")], 
                className = "ml-5", justify = "center", align = "center"),
				dcc.Dropdown(id='pollutant-dropdown-B', 
					options = [{'label': str(comp), 'value': str(comp)} for comp in df.pollutant_abb.unique()], 
					multi = False, value = "Nickel", placeholder = "Select pollutant", className = "ml-3 mr-3 mt-2 mb-2"),
                dbc.Row(dbc.Col(id = "pollutant-graph-B", width = 10), justify = "center"),
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
        
        
        bar_fig = px.bar(dff, x = "U_SAMPLE_DTTM", y = "DISPLAYVALUE", color = "SAMPLEDESC", title = "Pollutants by type",
                         labels = {"SAMPLEDESC": "Company"})
        bar_fig.update_layout({"yaxis": {"title": {"text": "Metals mg/L"}}})
        
        date_buttons2 = [
            {"count": 1, "step": "month", "stepmode": "backward", "label": "1MTD"},
            {"count": 6, "step": "month", "stepmode": "backward", "label": "6MTD"},
            {"count": 12, "step": "month", "stepmode": "backward", "label": "1YTD"},
            {"count": 12*3, "step": "month", "stepmode": "backward", "label": "3YTD"},
            {"count": (datetime.now().date() - dff["U_SAMPLE_DTTM"].min()).days, "step": "day", "stepmode": "backward", "label": "ALL"},
        ]
        
        bar_fig.update_layout({"yaxis": {"title": {"text": "Metals mg/L"}},
                                "xaxis": {"rangeselector": {"buttons": date_buttons2}, 
                                          "title": {"text": ""}}})
        
        return dcc.Graph(figure = bar_fig)
        
    else:
        bar_fig = px.bar(df, x = "U_SAMPLE_DTTM", y = "DISPLAYVALUE", color = "pollutant_abb", title = "Pollutants by type",
                         labels = {"pollutant_abb": "Pollutant"})
        
        date_buttons = [
            {"count": 1, "step": "month", "stepmode": "backward", "label": "1MTD"},
            {"count": 6, "step": "month", "stepmode": "backward", "label": "6MTD"},
            {"count": 12, "step": "month", "stepmode": "backward", "label": "1YTD"},
            {"count": 12*3, "step": "month", "stepmode": "backward", "label": "3YTD"},
            {"count": (datetime.now().date() - df["U_SAMPLE_DTTM"].min()).days, "step": "day", "stepmode": "backward", "label": "ALL"},
        ]
        
        bar_fig.update_layout({"yaxis": {"title": {"text": "Metals mg/L"}},
                               "xaxis": {"rangeselector": {"buttons": date_buttons}, 
                                         "title": {"text": " "}}})
        
        return dcc.Graph(figure = bar_fig)

####### TAB 2 ##############
@app.callback(
	[Output("pollutants-gauge-row-B", "children"), 
    Output("collapse-row-B", "children"),
	Output("pollutant-graph-B", "children"),
     Output("site-code-lbl-B", "children")],
	[Input("company-dropdown-B", "value"), Input("pollutant-dropdown-B", "value")]
)
def filterCompanyB(selected_company, selected_pollutant):
    if selected_company:
        if selected_pollutant:
            dff = df.loc[df.SAMPLEDESC.isin([selected_company])]
            dff["exceeds_limits"] = dff.apply(lambda row: row.DISPLAYVALUE > row.Limit, axis = 1)
            ## Order pollutants in descending order (% of timepoints exceeding limit)
            dff_aux = dff.groupby("pollutant_abb").exceeds_limits.mean().reset_index()
            pollutant_list = dff_aux.sort_values("exceeds_limits", ascending = False).pollutant_abb
            
            btn_lbl = selected_company
            
            # ------------ Pollutant gauges -------------
            POLLUTANT_STATS = [] # Container that will hold the gauge Divs
            POLLUTANT_COLLAPSE = [] # Container that will hold the gauge Divs in excess of the top 6
            gauge_color ={"gradient":True,"ranges":{"green":[0,30],"yellow":[30,60],"red":[60,100]}} # Customize the color of the gauges
      
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
               
            # ------------ Pollutant graph -------------
            if selected_pollutant:
                dff_pol = dff.loc[dff.pollutant_abb == selected_pollutant]
            else:
                dff_pol = dff
                
            dff_pol = dff_pol.sort_values("U_SAMPLE_DTTM").reset_index(drop = True)
            
            # PX FIG
            # fig_trend = px.line(dff_pol, x = "U_SAMPLE_DTTM", y = "DISPLAYVALUE")
            # fig_trend.update_layout({"xaxis": {"title": {"text": "Sample Datetime"}}, "yaxis": {"title": {"text": "Allowed limit (mg/L)"}}})
             
            # GO FIG
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x = dff_pol.U_SAMPLE_DTTM, y = dff_pol.DISPLAYVALUE, mode = "lines+markers")) # name = "first"
            fig_trend.add_trace(go.Scatter(x = dff_pol.U_SAMPLE_DTTM, y = dff_pol.Limit, line = dict(dash = "dash"), mode = "lines"))
            fig_trend.update_layout(xaxis_title = "Date", yaxis_title = "Mg/L", showlegend=False) # title = "Title", 
            
            return POLLUTANT_STATS, POLLUTANT_COLLAPSE, dcc.Graph(figure = fig_trend), btn_lbl
  
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