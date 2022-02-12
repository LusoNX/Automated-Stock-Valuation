import yfinance as yf 


import sklearn
from sklearn.linear_model import LinearRegression
import numpy as np 
from pandas import json_normalize
import pandas as pd 

import Yahoo_Multiples


## Instead of importing, you can call the Yahoo_Multiples function to have updated industry values. However this would take awhile... 

#df = Yahoo_Multiples.industry_Multiples("replace with adequate symbols")

df = pd.read_csv("industry_multiples_FINAL.csv")

##-------------------------------------------------------------------------------- Model 1 - DCF Valuation --------------------------------------------------------------------------------
## --------------------------------------------------------------------------------(A) FCF given by Yahoo ------------------------------------------------------------------------

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




def CF_data(symbol):
	ticker = yf.Ticker(symbol)

	df_quarterly = ticker.quarterly_cashflow
	df_quarterly = df_quarterly.T

	try:
		capex = df_quarterly["Capital Expenditures"]*(-1)
	except:
		capex = 0

	df_quarterly["fcf"] = df_quarterly["Total Cash From Operating Activities"] - capex
	df_quarterly["fcfe"] = df_quarterly["fcf"]+ df_quarterly["Net Borrowings"]
	fcf = df_quarterly["fcf"].sum()
	fcfe = df_quarterly["fcfe"].sum()
	return fcf,fcfe


CF_data("OHI")


def cost_of_equity(symbol):
	## For the Beta we use the yahoo 
	ticker = yf.Ticker(symbol)
	spy = yf.Ticker("^GSPC")
	beta = ticker.info["beta"]
	rm = 0.1 # Assumed long ter market return
	rf = 0.01375  # Later find an API for this value

	if beta is not None:
		ke = rf + beta*(rm-rf)
		ke = ke

		return ke
	else:
		price_stock = yf.download(symbol,start = "2017-01-01", end = "2022-01-01", interval = "1mo") ## Last five Years
		print(price_stock)
		returns_stock = price_stock.pct_change()
		returns_stock = returns_stock[returns_stock['Close'].notna()]

		price_index = yf.download("^GSPC",start = "2017-01-01", end = "2022-01-01",interval = "1mo")
		returns_index = price_index.pct_change()

		returns_index = returns_index[returns_index['Close'].notna()]

		final = returns_stock.merge(returns_index,on = "Date")

		X = np.c_[final["Close_x"]]
		Y = np.c_[final["Close_y"]]
		if len(X) >= 20: ## 1 Year of data

			lin_reg_model = sklearn.linear_model.LinearRegression().fit(X,Y)
			beta = lin_reg_model.coef_
			print(beta)
			ke = rf + beta*(rm-rf)
		else:
			ke = None
		
		return ke[0][0]



def cost_of_debt(symbol):
	ticker = yf.Ticker(symbol)
	df_quarterly = ticker.quarterly_financials
	df_quarterly = df_quarterly.T
	try:
		interest_exp = df_quarterly["Interest Expense"].sum()
	except KeyError:
		interest_exp = 0
	try:
		debt = ticker.info["totalDebt"]
	except KeyError:
		debt = 0
	tax_rate = 0.23
	kd = interest_exp*(1-tax_rate) / debt *(-1)
	return kd, debt


def wacc(symbol):
	ke = cost_of_equity(symbol)
	kd,debt = cost_of_debt(symbol)
	ticker = yf.Ticker(symbol)
	mkt_cap = ticker.info["marketCap"]
	total_cap = debt + mkt_cap
	weight_debt = debt / total_cap
	weight_equity = mkt_cap / total_cap

	wacc = ke*weight_equity + kd*weight_debt

	return wacc

## growth ASsumptions Code 
# "A1" . Perpetual 2 % growth . [MATURE COMPANIES]
# "A2" . Growth derived from PEG equation for 1 year and perpetual at 2 % thereafter [HIGH GROWTH COMPANIES]
# "A3" . Firm grows at current Rev growth rate (last 3 years) for 5 years and then converges to perpetual 2 %

# "A4". Firm grows at current Rev growth rate (last 3 years) for 5 years and then converges to perpetual 2 %



def dcf_valuation_A(symbol,growth_assumption):
	ke = cost_of_equity(symbol)
	kd,debt = cost_of_debt(symbol)
	ticker = yf.Ticker(symbol)
	fcf,fcfe = CF_data(symbol)
	mkt_cap = ticker.info["marketCap"]
	total_cap = debt + mkt_cap
	weight_debt = debt / total_cap
	weight_equity = mkt_cap / total_cap
	


	wacc = ke*weight_equity + kd*weight_debt

	shares_out = ticker.info["sharesOutstanding"]

	## Pick the industry ROE or growth rate 

	## Here we will be using different assumptions to forecast growth and time

	# (1) Perpetual Growth = 2 % (economy)

	if growth_assumption == "A1" and fcf != None:
		g = 0.02
		value = fcf*(1+g) / (wacc-g)
		value_per_share = value / shares_out
		value_per_share = value_per_share
		return value_per_share


	
	elif growth_assumption == "A2" and fcf != None:
		try:
			peg_ratio = ticker.info["pegRatio"]
			pe_ratio = ticker.info["trailingPE"]
			g_year_1 = pe_ratio/peg_ratio/100
			g = 0.02
			fcf_year_1 = (fcf*(1+g_year_1))
			value = (fcf_year_1/(1+wacc)) + (fcf_year_1*(1+g)/(wacc-g))/(1+wacc)**2
			value_per_share = value / shares_out
			value_per_share = value_per_share
			

		except :
			value_per_share = 0
			print("Assumption A2 is N/A")

		return value_per_share


	elif growth_assumption == "A3" and fcf != None:
		is_values = ticker.financials
		is_values = is_values.T
		is_values["Rev_growth"] = is_values["Total Revenue"].pct_change(-1)
		mean_return = is_values["Rev_growth"].mean()
		gs = mean_return
		discounted_fcf_list = []

		for i in range(1,6):
			discounted_fcf = (fcf *(1+gs)**i)/(1+wacc)**i
			x = discounted_fcf
			discounted_fcf_list.append(x)

		gl = 0.02	

		pv_value = sum(discounted_fcf_list)
		last_fcf = discounted_fcf_list[4]

		terminal_value = (last_fcf*(1+gl)/(wacc-gl))/(1+wacc)**5
		value_per_share = (terminal_value+pv_value)/shares_out
		value_per_share = value_per_share
		return value_per_share
			
		
	else:
		value_per_share = 0
		print("Introduced assumption is either nonvalid or nonexistent. Please use an approppriate assumption")

		return value_per_share




	

## Assumptins for the model
# B1 Simple Div GGM model with a perpetual 2 % growth rate
# B2 H-Model where growth rate is equal to ROE x retention_rate of the company, but converges to industry values. 5-Years Value


def div_valuation_B(symbol,assumption):
	ke = cost_of_equity(symbol)
	ticker = yf.Ticker(symbol)
	data = ticker.info
	div = data["dividendRate"]
	div_5_year_aver = data["fiveYearAvgDividendYield"] 
	div_yield = data["dividendYield"]
	eps = data["trailingEps"]


	if assumption == "B1":
		g = 0.02
		if ke > g and div != None:

			value_per_share = div/(ke-g)
			value_per_share = value_per_share

			
		else:
			print("Assumption B1 is N/A")
			value_per_share = 0



	if assumption == "B2":
		industry = ticker.info["industry"]
		industry_values = df[df["industry"] == industry]

		roe_lt = industry_values["returnOnEquity"].values[0]  ## Assumed industry convergence
		payout_lt = industry_values["payoutRatio"].values[0]
		retention_ratio_lt = 1- payout_lt
		gl = roe_lt*retention_ratio_lt


		# growth rate short term
		roe_st = ticker.info["returnOnEquity"]
		payout_st = ticker.info["payoutRatio"]
		retention_ratio_st = 1- payout_st
		if roe_st != None and retention_ratio_st != None:
			gs = roe_st*retention_ratio_st
		else:
			print("Assumption B2 is N/A")
			gs = 0
			value_per_share = 0

		if gs > 0 and gl > 0 and ke > gl and div != None:
			time_period = 5
			value_per_share = (div*(1+gl)/(ke-gl)) + (div*(time_period/2)*(gs-gl)/(ke-gl))
			value_per_share = value_per_share

		else:
			print("Assumpion B2 is N/A")
			value_per_share = 0

	return value_per_share




def analyst_valuation_C(symbol):
	ticker = yf.Ticker(symbol)
	target_price = ticker.info["targetMeanPrice"]
	analyst_nr = ticker.info["numberOfAnalystOpinions"]

	return target_price,analyst_nr





