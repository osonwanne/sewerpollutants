import dash
import dash_core_components as dcc
import dash_html_components as html 
import plotly.graph_objects as go
import pandas as pd


# Load data

url1 = 'https://sewerpollutants.s3.us-west-2.amazonaws.com/LIMS.xls'
df = pd.read_excel(url1,index_col=0, parse_dates=True)

# Plot data

app = dash.Dash()
server = app.server

app.layout = html.Div([dcc.Graph(id='barchart',
						figure = {'data':[
								go.Bar(
								x = df['U_SAMPLE_DTTM'],
    							y = df['DISPLAYVALUE'],
    							)], 
						'layout':go.Layout(title='Sewer Pollutants',
								yaxis_range=[0,2],
								yaxis_title_text='Metals ug/L'
								)}
						)])

if __name__ == "__main__":
        app.run_server()