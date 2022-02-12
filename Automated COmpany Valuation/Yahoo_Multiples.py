import yfinance as yf 
import time

import sklearn
from sklearn.linear_model import LinearRegression
import numpy as np 
from pandas import json_normalize
import pandas as pd 


## Notes on the FInancial data retrieved :

# 1. Total Revenue excludes any gains or losses from hedging derivatives


def IS_data(symbol):
	ticker = yf.Ticker(symbol)

	df_quarterly = ticker.quarterly_financials
	df_quarterly = df_quarterly.T
	df_annual = ticker.financials
	df_annual = df_annual.T

	df_annual["Ebit_Margin"] = df_annual["Ebit"] / df_annual["Total Revenue"]

	return df_annual, df_quarterly


def BS_data(symbol):
	ticker = yf.Ticker(symbol)

	df_annual = ticker.balance_sheet
	df_annual = df_annual.T

	df_annual["operating_assets"] = df_annual["Total Current Assets"] - df_annual["Cash"]
	df_annual["operating_liabilities"] = df_annual["Total Current Liabilities"] - df_annual["Cash"]

	df_quarterly =  ticker.quarterly_balance_sheet
	df_quarterly = df_quarterly.T
	df_quarterly["operating_assets"] = df_quarterly["Total Current Assets"] - df_quarterly["Cash"]





def CF_DATA(symbol):
	ticker = yf.Ticker(symbol)

	df_annual = ticker.quarterly_cashflow
	df_annual = df_annual.T





def ratios_dcf(symbol):
	bs_annual, bs_quarterly = BS_data(symbol)
	is_annual,is_quarterly = IS_data(symbol)

def cost_of_equity(symbol):

	## For the Beta we use the yahoo 
	ticker = yf.Ticker(symbol)
	spy = yf.Ticker("SPY")

	price_stock = ticker.history(start = "2020-11-06", end = "2021-11-06") ## Last five Years
	returns_stock = price_stock.pct_change()
	returns_stock = returns_stock[returns_stock['Close'].notna()]

	price_index = spy.history(start = "2020-11-06", end = "2021-11-06")
	returns_index = price_index.pct_change()
	returns_index = returns_index[returns_index['Close'].notna()]

	X = np.c_[returns_index["Close"]]
	Y = np.c_[returns_stock["Close"]]

	if len(X) == len(Y):

		lin_reg_model = sklearn.linear_model.LinearRegression().fit(X,Y)
		beta = lin_reg_model.coef_
		rm = 0.1 # Assumed long ter market return
		rf = 0.01375  # Later find an API for this value
		ke = rf + beta*(rm-rf)
	else:
		ke = None
	return ke


def industry_multiples(symbol):
	lista = []
	symbol_list = []

	stock_list = symbol
	for i in stock_list:
		try: 
			ticker = yf.Ticker(i)
			data = ticker.info
			lista.append(data)
			symbol_list.append(i)
			print(i)
			time.sleep(2)
		except KeyError:
			pass
			


	df = json_normalize(lista)
	df = df[["symbol","currentPrice","payoutRatio","shortPercentOfFloat","dividendYield","sector","market","industry","grossMargins","operatingMargins","profitMargins","returnOnAssets","returnOnEquity","debtToEquity","trailingPE","priceToBook","heldPercentInsiders","enterpriseToEbitda","heldPercentInstitutions","numberOfAnalystOpinions","targetMeanPrice"]]
	df.to_csv("multiples.csv")

	df_industry= df.groupby("industry",as_index = False).mean()
	df_industry = df_industry.fillna(0)
	df_sector= df.groupby("industry",as_index = False).mean()
	df_sector = df_sector.fillna(0)
	df_sector.to_csv("sector.csv")

	return df, df_industry

