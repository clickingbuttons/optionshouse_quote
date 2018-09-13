from urllib import request, parse
from pathlib import Path
import datetime
import configparser
import time
import json
import pickle

import numpy as np
import plotly
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import pyimgur


default_url = "https://trading.etrade.com/jsonServices/chartsData/v3"
config = configparser.RawConfigParser()   
config.read(str(Path.home()) + "/.etrade/etrade.conf")
panics = [
	("POTN", "02/14/2018", "https://profit.ly/1Mv4uR"),
	("CRON", "03/01/2018", "https://profit.ly/1Mv8Za"),
	("POTN", "03/07/2018", "https://profit.ly/1Mv9xm"),
	("ECYT", "03/12/2018", "https://profit.ly/1MvAzq"),
	("GOPH", "03/13/2018", "https://profit.ly/1MvBHc"),
	("CRON", "03/20/2018", "https://profit.ly/1MvDFP"),
	("LIQT", "03/21/2018", "https://profit.ly/1MvDSD"),
	("FUSZ", "03/28/2018", "https://profit.ly/1MvFJE"),
	("GOPH", "04/05/2018", "https://profit.ly/1MvH39"),
	("GOPH", "04/12/2018", "https://profit.ly/1MvIol"),
	("CANN", "04/17/2018", "https://profit.ly/1MvK3d"),
	("CANN", "04/18/2018", "https://profit.ly/1MvKJc"),
	("CANN", "04/23/2018", "https://profit.ly/1MvLoC"),
	("FUSZ", "04/24/2018", "https://profit.ly/1MvLwm"),
	("TZOO", "04/25/2018", "https://profit.ly/1MvM5x"),
	("FUSZ", "04/26/2018", "https://profit.ly/1MvMK4"),
	("FUSZ", "04/27/2018", "https://profit.ly/1MvMbS"),
	("LRGR", "04/27/2018", "https://profit.ly/1MvMcY"),
	("ZAGG", "05/09/2018", "https://profit.ly/1MvPHh"),
	("HEAR", "05/09/2018", "https://profit.ly/1MvPIf"),
	("APRN", "05/09/2018", "https://profit.ly/1MvPGW"),
	("HEAR", "05/11/2018", "https://profit.ly/1MvPpy"),
	("SORL", "05/15/2018", "https://profit.ly/1MvQiH"),
	("SORL", "05/15/2018", "https://profit.ly/1MvQiH"),
	("FUSZ", "05/21/2018", "https://profit.ly/1MvT0K"),
	("JVA", "06/07/2018", "https://profit.ly/1MvXH6"),
	("SNES", "06/11/2018", "https://profit.ly/1MvYbV"),
	("DEST", "06/14/2018", "https://profit.ly/1Mva50"),
	("EGY", "06/15/2018", "https://profit.ly/1MvaHQ"),
	("GEVO", "06/22/2018", "https://profit.ly/1Mvc8w"),
	("RKDA", "06/27/2018", "https://profit.ly/1Mvd8S"),
	("ABIL", "06/28/2018", "https://profit.ly/1MvdPd"),
	("MXC", "07/02/2018", "https://profit.ly/1Mveam"),
	("CEI", "07/13/2018", "https://profit.ly/1MvhDw"),
	("CODA", "07/16/2018", "https://profit.ly/1Mvhda"),
	("CRON", "07/18/2018", ""),
	("SRAX", "07/18/2018", "https://profit.ly/1Mvhx5"),
	("CVSI", "07/24/2018", "https://profit.ly/1MvjR5"),
	("LUNA", "08/03/2018", "https://profit.ly/1Mvkic"),
	("NVTA", "08/08/2018", "https://profit.ly/1MvlQo"),
	("STAF", "08/15/2018", "https://profit.ly/1Mvorn"),
	("CVSI", "08/21/2018", "https://profit.ly/1Mvpcj"),
	("CVSI", "08/23/2018", "https://profit.ly/1MvqBJ"),
	("CVSI", "08/29/2018", "https://profit.ly/1MvrsZ"),
	("INSY", "08/31/2018", "https://profit.ly/1MvsMF"),
	("CLOW", "09/05/2018", "https://profit.ly/1Mvt2T"),
	("CLOW", "09/06/2018", "https://profit.ly/1MvtHG"),
	("CRON", "09/11/2018", ""),
	("HYYDF", "09/11/2018", ""),
	("GERN", "09/12/2018", ""),
]
spreadsheet_id = "1AsuAI6ZXjcMh_uD7kIKs_oKIZ7wKKiE37TQ7F98Hv-E"
spreadsheet_scopes = "https://www.googleapis.com/auth/spreadsheets"
imgur = pyimgur.Imgur(open("imgur_clientid", "r").read())

def date_to_unix(date):
	return int(time.mktime(date.timetuple()))

def get_stock(symbol, from_date, to_date, freq):
	payload = {"getChartData": {
		"delayed": False,
		"retrieveVolatility": False,
		"includeExtendedHours": True,
		"instrumentType": "Equity",
		"studiesMaxPeriod": 15}}
	payload["getChartData"]["symbol"] = symbol
	payload["getChartData"]["frequency"] = freq
	payload["getChartData"]["fromTimestamp"] = date_to_unix(from_date) * 1000
	payload["getChartData"]["toTimestamp"] = date_to_unix(to_date) * 1000

	headers = {
		"Content-Type": "application/json;charset=UTF-8",
		"Cookie": config.get("etrade", "cookie"),
		"token": config.get("etrade", "token")
	}

	req =  request.Request(default_url,
		data=json.dumps(payload).encode("utf-8"),
		headers=headers)
	return json.loads(request.urlopen(req).read())

def get_candles(symbol, from_date, to_date, freq=1):
	chart_data = get_stock(symbol, from_date, to_date, freq)
	candles = chart_data["getChartDataResponse"]["results"]["candles"]
	for c in candles:
		c["date"] = datetime.datetime.strptime(c["Date"], "%Y-%m-%d %H:%M:%S")
		del c["Date"]
	return candles

def is_market(time):
	if time >= datetime.time(9, 30) and time < datetime.time(16, 0):
		return True
	return False

def is_between(time, time1, time2):
	if time >= time1 and time < time2:
		return True
	return False

def premarket_open_close(candles):
	premarket_candles = [c for c in candles if not is_market(c["date"].time())]
	# print(premarket_candles)
	return (premarket_candles[0]["open"], premarket_candles[-1]["close"])

def market_open_close(candles):
	market_candles = [c for c in candles if is_market(c["date"].time())]
	return (market_candles[0]["open"], market_candles[-1]["close"])

def morning_min(candles, from_time, to_time):
	morning_candles = [c for c in candles
		if is_between(c["date"].time(), from_time, to_time)]
	return min(morning_candles, key=lambda c: c["low"])

def morning_max(candles, from_time, to_time):
	morning_candles = [c for c in candles
		if is_between(c["date"].time(), from_time, to_time)]
	return max(morning_candles, key=lambda c: c["high"])

def morning_panic_stats(candles):
	# print("Finding panic in first hour of market...", end="")
	panic = morning_min(candles, datetime.time(9, 30), datetime.time(10, 30))
	# print("found", panic)
	# print("Rewinding to find when the panic started...", end="")
	panic_start = morning_max(candles, datetime.time(9, 29), panic["date"].time())
	# print("found", panic_start)
	# print("Finding rebound in first hour after panic end...", end="")
	rebound = morning_max(candles, panic["date"].time(), (panic["date"] + datetime.timedelta(hours=1)).time())
	# print("found", rebound)

	return {
		"Previous close": candles[0]["close"],
		"Premarket open": premarket_open_close(candles)[0],
		"Premarket close": premarket_open_close(candles)[1],
		"Open": market_open_close(candles)[0],
		"Panic Start": panic_start["date"].time(),
		"Panic Start Max": panic_start["high"],
		"Panic End": panic["date"].time(),
		"Panic Min": panic["low"],
		"Bounce End": rebound["date"].time(),
		"Bounce Max": rebound["high"],
	}

def make_annotation(x, y, text, down=False):
	return dict(
		x=x,
		y=y,
		xref="x",
		yref="y",
		text=text,
		showarrow=True,
		font=dict(
			family='Courier New, monospace',
			size=16,
			color='#ffffff'
		),
		align='center',
		arrowhead=2,
		arrowsize=1,
		arrowwidth=2,
		arrowcolor='#636363',
		ax=20,
		ay=30 if down else -30,
		bordercolor='#c7c7c7',
		borderwidth=2,
		borderpad=4,
		bgcolor='#ff7f0e',
		opacity=0.8
	)

def add_time(date_time, time):
	# Add a time to a date...
	return date_time + datetime.timedelta(hours=time.hour, minutes=time.minute)

def make_annotations(stats):
	return [ 
		make_annotation(
			add_time(stats["Date"], stats["Panic Start"]),
			stats["Panic Start Max"], "Panic Start $" + str(stats["Panic Start Max"])),
		make_annotation(
			add_time(stats["Date"], stats["Panic End"]),
			stats["Panic Min"], "Panic End $" + str(stats["Panic Min"]), down=True),
		make_annotation(
			add_time(stats["Date"], stats["Bounce End"]),
			stats["Bounce Max"], "Bounce End $" + str(stats["Bounce Max"])),
	]

def make_plot(candles, stats):
	trace0 = plotly.graph_objs.Candlestick(
		name="price",
		x=[c["date"] for c in candles],
		open=[c["open"] for c in candles],
		high=[c["high"] for c in candles],
		low=[c["low"] for c in candles],
		close=[c["close"] for c in candles])

	trace1 = plotly.graph_objs.Bar(
		name="volume",
		marker=dict(
			color=[1 if c["close"] > c["open"] else 0 for c in candles],
			colorscale=[[0, "rgba(255, 52, 52, 0.7)"], [1, "rgba(52, 255, 52, 0.7)"]]
		),
		x=[c["date"] for c in candles],
		y=[c["volume"] for c in candles],
		yaxis="y2")
	layout = plotly.graph_objs.Layout(
		title=stats["Symbol"],
		showlegend=False,
		xaxis=dict(
			title="time",
			range=[stats["Date"] + datetime.timedelta(hours=9, minutes=30),
				   stats["Date"] + datetime.timedelta(hours=12)],
			type="date"
		),
		yaxis=dict(
			title="price"
		),
		yaxis2=dict(
			title="volume",
			overlaying="y",
			side="right",
			range=[0, max([c["volume"] for c in candles]) * 5]
		),
		annotations=make_annotations(stats)
	)
	fig = plotly.graph_objs.Figure(data=[trace0, trace1], layout=layout)
	return fig

def make_stats(symbol, date, url, candles):
	basic_stats = dict(
		name="_".join([symbol, "panic", date.strftime("%m-%d-%Y")]),
		Symbol=symbol,
		Date=date,
		URL=url
	)
	return dict(basic_stats, **morning_panic_stats(candles))

def pretty_for_spreadsheet(value):
	if type(value) is datetime.datetime:
		return value.strftime("%Y-%m-%d")
	elif type(value) is datetime.time:
		return value.strftime("%H:%M")
	# elif type(value) is str and value.startswith("https://i.imgur.com"):
	# 	return '=IMAGE("{}")'.format(value)
	return value

def write_spreadsheet_row(service, index, values):
	values = [pretty_for_spreadsheet(v) for v in values]
	service.spreadsheets().values().append(
		spreadsheetId=spreadsheet_id,
		range="Sheet1!A1:Z1",
		valueInputOption="USER_ENTERED",
		body=dict(
				range="Sheet1!A1:Z1",
				majorDimension="ROWS",
				values=[values]
			)
		).execute()

def format_header(service):
	reqs = {'requests': [
		# embolden row 1
		{'repeatCell': {
			'range': {'endRowIndex': 1},
			'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
			'fields': 'userEnteredFormat.textFormat.bold',
		}}
	]}
	service.spreadsheets().batchUpdate(
		spreadsheetId=spreadsheet_id,
		body=reqs).execute()

def write_headers(service, keys):
	write_spreadsheet_row(service, 0, list(keys))
	format_header(service)

def clear_spreadsheet(service):
	service.spreadsheets().values().clear(
			spreadsheetId=spreadsheet_id,
			range="Sheet1!A1:Z1000"
		).execute()

def write_spreadsheet(stats):
	store = file.Storage('token.json')
	creds = store.get()
	if not creds or creds.invalid:
		flow = client.flow_from_clientsecrets('credentials.json', spreadsheet_scopes)
		creds = tools.run_flow(flow, store)
	service = build('sheets', 'v4', http=creds.authorize(Http()))

	clear_spreadsheet(service)
	write_headers(service, stats[0].keys())
	for i, v in enumerate(stats):
		write_spreadsheet_row(service, i + 1, v.values())

def calculate_panic_stats():
	print("Calculating stats...")
	all_stats = []
	for symbol, date, url in panics:
		print("\t" + symbol + "...", end="")
		panic_date = datetime.datetime.strptime(date, "%m/%d/%Y")

		candles = get_candles(symbol,
			panic_date - datetime.timedelta(hours=8),
			panic_date + datetime.timedelta(days=1))
		if not candles:
			print("no chart data")
			continue
		stats = make_stats(symbol, panic_date, url, candles)

		fig = make_plot(candles, stats)
		plotly.offline.plot(fig, filename="charts/" + stats["name"] + ".html")
		# To write_image you need to:
		# 	$ npm install -g electron@1.8.4 orca
		# 	$ pip install psutil
		# 	https://plot.ly/python/static-image-export/
		plotly.io.write_image(fig, "images/" + stats["name"] + ".png")

		all_stats.append(stats)
		print("done")

	return all_stats

def imgur_upload(stats):
	# print("Uploading charts to imgur...")
	# for s in stats:
	# 	fname = "images/" + s["name"] + ".png"
	# 	print("\t" + fname + "...", end="")
	# 	uploaded_image = imgur.upload_image(fname, title=s["name"])
	# 	s["Chart"] = uploaded_image.link
	# 	del s["name"]
	# 	print("done")

# Maybe do indexes: SPY	QQQ	RUT
if __name__ == "__main__":
	all_stats = calculate_panic_stats()
	# all_stats = pickle.load(open("all_stats.pickle", "rb"))
	print(all_stats)
	pickle.dump(all_stats, open("all_stats.pickle", "wb"))

	imgur_upload(all_stats)
	pickle.dump(all_stats, open("all_stats.pickle", "wb"))

	print("Uploading stats and charts to google sheets...")
	write_spreadsheet(all_stats)
