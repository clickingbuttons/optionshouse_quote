from urllib import request, parse
from pathlib import Path
import datetime
import configparser
import time
import json
import numpy as np
import plotly


default_url = "https://trading.etrade.com/jsonServices/chartsData/v3"
config = configparser.RawConfigParser()   
config.read(str(Path.home()) + '/.etrade/etrade.conf')


def date_to_unix(date):
	return int(time.mktime(date.timetuple()))

def get_stock(symbol, from_date, to_date, freq=1):
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
		"Cookie": config.get('etrade', 'cookie'),
		"token": config.get('etrade', 'token')
	}

	req =  request.Request(default_url,
		data=json.dumps(payload).encode("utf-8"),
		headers=headers)
	return json.loads(request.urlopen(req).read())

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
	# Find panic in first hour of market
	panic = morning_min(candles, datetime.time(9, 30), datetime.time(10, 30))
	# Rewind to find when the panic started
	panic_start = morning_max(candles, datetime.time(9, 30), panic["date"].time())
	# Find rebound top in first hour after panic
	rebound = morning_max(candles, panic["date"].time(), (panic["date"] + datetime.timedelta(hours=1)).time())

	return {
		# "Previous close": candles[0]["close"],
		# "Premarket open": premarket_open_close(candles)[0],
		# "Premarket close": premarket_open_close(candles)[1],
		# "Open": market_open_close(candles)[0],
		"Panic Start": panic_start["date"].time(),
		"Panic End": panic["date"].time(),
		# "Panic Min": panic["low"],
		"Bounce End": rebound["date"].time(),
		# "Bounce Max": rebound["high"],
	}

def plot_chart(candles):
	trace0 = plotly.graph_objs.Candlestick(
		name="price",
		x=[c["date"] for c in candles],
		open=[c["open"] for c in candles],
		high=[c["high"] for c in candles],
		low=[c["low"] for c in candles],
		close=[c["close"] for c in candles])

	min_price = min([c["low"] for c in candles])
	max_price = max([c["high"] for c in candles])
	max_volume = max([c["volume"] for c in candles])

	# Range to work with
	height = max_price - min_price
	max_vol = max([c["volume"] for c in candles])
	# trace1 = plotly.graph_objs.Bar(
	# 	x=[c["date"] for c in candles],
	# 	y=[c["volume"] * height * .2 / max_volume for c in candles],
	# 	base=[min_price * .8 for _ in candles])
	trace1 = plotly.graph_objs.Bar(
		name="volume",
		marker={
			"color": [1 if c["close"] > c["open"] else 0 for c in candles],
			"colorscale": [[0, 'rgba(255, 52, 52, 0.7)'], [1, 'rgba(52, 255, 52, 0.7)']]
		},
		x=[c["date"] for c in candles],
		y=[c["volume"] for c in candles],
		yaxis="y2")
	layout = plotly.graph_objs.Layout(
		title=symbol,
		xaxis={
			"title": "time",
			"range": [panic_date + datetime.timedelta(hours=9, minutes=30),
					  panic_date + datetime.timedelta(hours=16)],
			"type": "date"
		},
		yaxis={
			"title": "price"
		},
		yaxis2={
			"title": "volume",
			"overlaying": "y",
			"side": "right",
			"range": [0, max_vol * 5]
		}
	)
	fig = plotly.graph_objs.Figure(data=[trace0, trace1], layout=layout)
	plotly.offline.plot(fig)
	# To write_image you need to:
	# 	$ npm install -g electron@1.8.4 orca
	# 	$ pip install psutil
	# 	https://plot.ly/python/static-image-export/
	plotly.io.write_image(fig, 'fig1.png')

# Maybe do indexes: SPY	QQQ	RUT
if __name__ == '__main__':
	panics = [
		# ("CRON", "07/18/2018"),
		# ("SRAX", "07/18/2018"),
		# ("CVSI", "07/24/2018"),
		# ("LUNA", "08/03/2018"),
		# ("NVTA", "08/08/2018"),
		# ("STAF", "08/15/2018"),
		# ("CVSI", "08/21/2018"),
		# ("CVSI", "08/23/2018"),
		# ("CVSI", "08/29/2018"),
		# ("INSY", "08/31/2018"),
		# ("CLOW", "09/05/2018"),
		# ("CLOW", "09/06/2018")
		("CRON", "09/11/2018")
		# ("HYYDF", "09/11/2018")
		# ("GERN", "09/12/2018")
	]
	stats = []
	for symbol, date in panics:
		panic_date = datetime.datetime.strptime(date, "%m/%d/%Y")

		chart_data = get_stock(symbol,
			panic_date - datetime.timedelta(hours=8),
			panic_date + datetime.timedelta(days=1))
		candles = chart_data["getChartDataResponse"]["results"]["candles"]
		# Pretty dates
		for c in candles:
			c["date"] = datetime.datetime.strptime(c["Date"], "%Y-%m-%d %H:%M:%S")
			del c["Date"]
		# print(candles)

		plot_chart(candles)

		basic_stats = {
			"Symbol": symbol,
			"Date": panic_date.strftime("%Y-%m-%d")
			}
		# Exploit dict contrstructor
		stats.append(dict(basic_stats, **morning_panic_stats(candles)))

	print(stats)
