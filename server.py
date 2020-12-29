from flask import Flask, render_template
from datetime import datetime, timedelta
import plotly.express as px
import pandas as pd 
import folium 
import branca
import re

app = Flask('covid')

@app.route('/')
def index():
	# total_cases, total_active, total_deaths = get_startup_data()
	total_cases, total_active, total_deaths, ticker_data = get_startup_data()
	return render_template('index.html', total_cases=total_cases, total_active=total_active, total_deaths=total_deaths, ticker_data=ticker_data)

def show_map(df):
	m = folium.Map(tiles='Stamen Watercolor', width='100%', height='100%', zoom_start=1, min_zoom=1, worldCopyJump=True)
	for i in range(0,len(df)):
		if pd.isna(df.iloc[i]['Long_']) or pd.isna(df.iloc[i]['Lat']) or pd.isna(df.iloc[i]['Country_Region']) or pd.isna(df.iloc[i]['Confirmed']):
			continue
		else:
			html = bubble(df, i)
			iframe = branca.element.IFrame(html=html, width=150, height=200)
			popup = folium.Popup(iframe,parse_html=True)
			folium.Circle(
				location=[float(df.iloc[i]['Lat']), float(df.iloc[i]['Long_'])],
				popup=popup,
				radius=float(df.iloc[i]['Confirmed'])/6,
				color='#d0312d',
				fill=True,
				fill_color='#d0312d',
				fill_opacity=1,
				prefer_canvas=True
			).add_to(m)
	m.save('templates/map.html')

def get_startup_data():
	cases_data = read_data()
	# show_map(cases_data)
	# build_global_plot()
	total_cases = get_total_global_cases(cases_data)
	total_active = get_total_active_global_cases(cases_data)
	total_deaths = get_total_global_deaths(cases_data)
	ticker_data = get_ticker_data(cases_data)
	get_country_list(cases_data)
	return total_cases, total_active, total_deaths, ticker_data

def get_ticker_data(df):
	df = df[df['Country_Region'] == "Canada"]
	df = df.drop(['FIPS', 'Admin2', 'Country_Region', 'Last_Update', 'Lat', 'Long_', 'Combined_Key', 'Incidence_Rate', 'Case-Fatality_Ratio'], axis=1)
	df.dropna(inplace=True)
	df['Active'].astype('int64')
	return df

def get_country_list(df):
	unq = df['Country_Region'].unique()
	cl = pd.DataFrame(columns=['Country', 'Total_Cases'])
	dl = pd.DataFrame(columns=['Country', 'Total_Deaths'])
	for i in unq:
		subset = df[df['Country_Region'] == i]
		cl = cl.append({'Country' : i, 'Total_Cases' : subset['Confirmed'].sum()}, ignore_index=True)
		dl = dl.append({'Country' : i, 'Total_Deaths' : subset['Deaths'].sum()}, ignore_index=True)
	cl.sort_values(by=['Total_Cases'], inplace=True, ascending=False)
	dl.sort_values(by=['Total_Deaths'], inplace=True, ascending=False)
	text_file = open("templates/cl.html", "w")
	text_file.write(cl.to_html(index=False, justify='center'))
	text_file.close()
	text_file = open("templates/dl.html", "w")
	text_file.write(dl.to_html(index=False, justify='center'))
	text_file.close()

def build_global_plot():
	df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
	df = df.drop(['Province/State', 'Country/Region', 'Lat', 'Long'], axis=1)
	l = list()
	for col in df.columns:
		l.append(df[col].sum())
	d = {'Date': df.columns, 'Cases': l}
	df = pd.DataFrame(data=d)
	fig = px.line(df, x="Date", y="Cases")
	fig.write_html('templates/global_cases_plot.html')

def read_data():
	today = datetime.now()
	yesterday = today - timedelta(days=1)
	cases_data = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{}.csv'.format(yesterday.strftime('%m/%d/%Y').replace('/','-')))
	return cases_data 

def get_total_global_cases(df):
	return df['Confirmed'].sum()

def get_total_active_global_cases(df):
	return int(df['Active'].sum())

def get_total_global_deaths(df):
	return df['Deaths'].sum()

def bubble(df, i):
	s = df.iloc[i]['Combined_Key']
	cases = str(df.iloc[i]['Confirmed'])
	deaths = str(df.iloc[i]['Deaths'])
	active = str(int(df.iloc[i]['Active']))

	html = """<!DOCTYPE html>
		<html>
		<head>
		<h4 style="margin-bottom:0"; width="300px">%s</h4>
		</head>
		<style type="text/css">
		.tg{border-collapse:collapse;border-spacing:0;}
		.tg td{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
		  overflow:hidden;padding:10px 5px;word-break:normal;}
		.tg th{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
		  font-weight:normal;overflow:hidden;padding:10px 5px;word-break:normal;}
		.tg .tg-qidm{background-color:#fc6f6f;border-color:#ffffff;color:#ffffff;text-align:left;vertical-align:top}
		.tg .tg-ucns{background-color:#cb0000;border-color:#ffffff;text-align:left;vertical-align:top}
		</style>
		<table class="tg">
		<thead>
		  <tr>
		    <th class="tg-ucns"><span style="color:#FFF">Cases</span></th>
		    <th class="tg-qidm">%s</th>
		  </tr>
		</thead>
		<tbody>
		  <tr>
		    <td class="tg-ucns"><span style="color:#FFF">Active</span></td>
		    <td class="tg-qidm">%s</td>
		  </tr>
		  <tr>
		    <td class="tg-ucns"><span style="color:#FFF">Deaths</span></td>
		    <td class="tg-qidm">%s</td>
		  </tr>
		</tbody>
		</table>
		</html> """ % (s, cases, active, deaths)
	return html

if __name__ == '__main__':
	app.run(debug = True)