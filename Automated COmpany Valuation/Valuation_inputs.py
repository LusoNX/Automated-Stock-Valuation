
## ---------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------
											 # # # STOCK SCREENER # # # 

# This is a stock screener that firstly screenes accordingly to a specific parameter and then evaluates the stock and compares it with its current price

# Use of ALpha Vantage API.
# The screener ignores ~stocks not having the last quarter data 
# It sums the  4 last quarters for evaluation 
# Only considers historical data


import requests
from pandas import json_normalize
import pandas as pd 
import time
import numpy as np 



api_key = "YOUR API KEY"

def make_request (method, function, symbol, api_key):
	if method == "GET":
		base_url = "https://www.alphavantage.co/query?"
		response = requests.get(base_url+"function=" +function +"&symbol="+symbol +"&apikey="+api_key)
		return response.json()


def price_data(symbol):
	r = make_request("GET","GLOBAL_QUOTE",symbol, api_key)
	df = json_normalize(r)
	try:
		if df["Global Quote.01. symbol"] is not None:
			df["price"] = df["Global Quote.05. price"]
			df["symbol"] = df["Global Quote.01. symbol"]
			price = df["price"].iloc[0]
			return price
	except KeyError:
		#print("Error found")
		pass

def get_overview(symbol):
	r = make_request("GET","OVERVIEW",symbol,api_key)
	df = json_normalize(r)
	return r,df


def get_balance_sheet(symbol):
	r = make_request("GET","BALANCE_SHEET",symbol,api_key)
	try:
		if r["annualReports"] is not None:
			r = r["annualReports"]
			df = json_normalize(r)
			df = df.iloc[::-1]
			return df
	except KeyError:
		pass

def get_income_statement(symbol):
	r = make_request("GET","INCOME_STATEMENT",symbol,api_key)
	#print(r["annualReports"])
	try:
		if r["annualReports"] is not None:# and r["annualReports"][0]["ebit"] != "None":
			r = r["annualReports"]
			df = json_normalize(r)
			df = df.replace('None', np.nan).dropna(how='all')
			df = df.iloc[::-1]
			return df
	except KeyError:
		pass


def get_cash_flow(symbol):
	r = make_request("GET","CASH_FLOW",symbol,api_key)
	r = r["quarterlyReports"]
	df = json_normalize(r)
	return df



def str_converter(r,column_name):
	lista = []
	for i in r:
		x =str(i)
		lista.append(x)
	df = pd.DataFrame({column_name:lista}).replace("None",0)
	df = df.astype(float)

	return df


def bs_variables(symbol):
	df = get_balance_sheet(symbol)
	if df is not None:
		try:
			df = df[0:5] ## last 5 years

			df["short_term_debt"] = str_converter(df["shortTermDebt"],"short_term_debt")
			df["long_term_debt"] = str_converter(df["longTermDebtNoncurrent"],"long_term_debt")
			df["TOTAL_DEBT"] =df["long_term_debt"] +df["short_term_debt"]


			# # # ----------------------------Operating Assets--------------- # # #
			# Working Capital
			df["current_assets"] = str_converter(df["totalCurrentAssets"],"current_assets")
			df["cash_and_equivalents"] = str_converter(df["cashAndShortTermInvestments"],"cash_and_equivalents")
			df["operating_short_assets"] = df["current_assets"]- df["cash_and_equivalents"]

			df["current_liabilities"] = str_converter(df["totalCurrentLiabilities"],"current_liabilities")
			df["NWC"] = df["operating_short_assets"] - df["current_liabilities"]

			# Fixed assets
			df["total_assets"] = str_converter(df["totalAssets"],"total_assets")
			df["current_assets"] = str_converter(df["totalCurrentAssets"],"current_assets")
			df["non_current_assets"] = df["total_assets"]- df["current_assets"]

			df["intangibles"] = str_converter(df["intangibleAssets"],"intangibles")
			df["fixed_assets"] = df["non_current_assets"] -df["intangibles"]



			# # # ---------------------------- Non Operating Assets ---------- # # #
			df["non_operating_assets"] =  df["cash_and_equivalents"]


			# Values for valuation 
			df["change_NWC"] = df["NWC"] - df["NWC"].shift(1)
			df["GCAPEX"] = df["fixed_assets"] -df["fixed_assets"].shift(1)
			#df["variation_debt"] = df["TOTAL_DEBT"] - df["TOTAL_DEBT"].shift(1) 
			
			#df["currentDebt"] = str_converter(df["currentDebt"],"currentDebt")
			#df["longTermDebtNoncurrent"] = str_converter(df["longTermDebtNoncurrent"],"longTermDebtNoncurrent")
			df = df[["fiscalDateEnding","NWC","change_NWC","GCAPEX", "commonStockSharesOutstanding","TOTAL_DEBT"]]
			#df.to_csv("AR_BS.csv")
			return df
		except KeyError:
			pass

	else:
		pass


#bs_variables("TSLA")
def is_variables(symbol):
	df = get_income_statement(symbol)
	if df is not None:
		
		df["totalRevenue"] = pd.to_numeric(df["totalRevenue"], downcast="float")
		df["interest_expense"] = str_converter(df["interestAndDebtExpense"],"interest_expense")

		df["ebit"] = pd.to_numeric(df["ebit"], downcast="float")
		df = df[0:5]
		df = df[["fiscalDateEnding","totalRevenue","ebit", "netIncome","interest_expense"]]
		return df
	else:
		return None




# # # Stock DCF Evaluation  # # #

def cost_of_equity(symbol):
	r,df = get_overview(symbol)

	beta = float(df["Beta"][0])
	rm = 0.1 # Assumed long ter market return
	rf = 0.01375  # Later find an API for this value
	ke = rf + beta*(rm-rf)
	return ke

#cost_of_equity("TSLA")

def final_variables(symbol):
	df_bs = bs_variables(symbol)
	df_is = is_variables(symbol)

	price = price_data(symbol)
	#ke = cost_of_equity(symbol)
	if df_bs is not None and df_is is not None:
		df_final =df_bs.merge(df_is, on = "fiscalDateEnding")
		df_final = df_final.rename(columns = {"fiscalDateEnding": "Date" , "totalRevenue":"Revenues","ebit":"EBIT"})
		return df_final,price
	else:
		return None,None



#cost_of_equity("AR")
def dcf_valuation(symbol):
	T = 0.23 # Assumed tax expense
	D = 0.1 #discount rate
	#ke = cost_of_equity(symbol)
	#df_bs = bs_variables(symbol)
	#df_is = is_variables(symbol)
	if df_bs is not None and df_is is not None :
		df_is["ebit"] = df_is["ebit"].astype(float)
		df_is["interestExpense"] = df_is["interestExpense"].astype(float)
		df_is["interestIncome"] = df_is["interestIncome"].astype(float)
		df_is["net_interest"] = df_is["interestIncome"]-df_is["interestExpense"]


		# FCFF valuation
		fcff = df_is["ebit"][0:4].sum()*(1-T) - df_bs["change_NWC"][0:4].sum()#+df_bs["Growth_CAPEX"] ## CALCULTATES THE FCFF
		fcff_per_share = fcff/float(df_bs["commonStockSharesOutstanding"][0])
		#annual_fcff_per_share = fcff_per_share[0:4].sum() # Sums last 4 quarter fcff
		value_fcff_per_share= fcff_per_share/D # 10% discount rate

		#FCFE Valuation
		fcfe = fcff - df_is["net_interest"][0:4].sum()*(1-T) + df_bs["variation_debt"][0:4].sum()
		fcfe_perpetuity_value = fcfe/ke
		value_fcfe = fcfe_perpetuity_value + df_bs["TOTAL_DEBT"][0] -df_bs["non_operating_assets"][0]
		value_fcfe_per_share = value_fcfe/float(df_bs["commonStockSharesOutstanding"][0])


		print(f"This is the estimated value for {symbol}. FCFF: {value_fcff_per_share}")
		print(f"This is the estimated value for {symbol}. FCFE : {value_fcfe_per_share}")
	else:
		print(f"Not Applicable with {symbol} having a None parameter")


