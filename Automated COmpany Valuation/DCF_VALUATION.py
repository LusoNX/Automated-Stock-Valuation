
## ---------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------
											 # # # STOCK SCREENER # # # 

# This is a stock screener that firstly screenes accordingly to a specific parameter and then evaluates the stock and compares it with its current price
# The screener ignores ~stocks not having the last quarter data 
# It sums the  4 last quarters for evaluation 
# Only considers historical data


import requests
from pandas import json_normalize
import pandas as pd 
import time
import numpy as np 
import matplotlib.pyplot as plt
import Valuation_inputs

import sklearn
from sklearn.linear_model import LinearRegression

api_key = "YOUR API KEY"





def dcf_valuation(symbol):
	df, price = Valuation_inputs.final_variables(symbol)
	ke = Valuation_inputs.cost_of_equity(symbol)
	if df is not None and price is not None and ke is not None:
		tax_rate = 0.23
		price = float(price)
		debt = float(df["TOTAL_DEBT"].iloc[-1])
		if debt != 0:
			cost_of_debt = float(df["interest_expense"].iloc[-1]*(-1) /df["TOTAL_DEBT"].iloc[-1])
			if cost_of_debt <0: ## If net Interest expense is positive, means cost_of_debt is negative, and thus we put it as 0
				kd =0
			else:
				kd = cost_of_debt
		else:
			kd = 0

		shares_outs = float(df["commonStockSharesOutstanding"].iloc[-1])

		mkt_cap = price*shares_outs
		wacc = ke*(mkt_cap/(mkt_cap+debt)) + kd*(1-tax_rate)*(debt/(mkt_cap+debt))

		## Revenue Estimationb
		
		df["Revenues"] = pd.to_numeric(df["Revenues"], downcast="float")

		df["change_%_revenue"] = df["Revenues"].pct_change(1)
		mean_change_revenue = df["change_%_revenue"].mean()
		std_change_revenue = df["change_%_revenue"].std()

		## EBIT Estimation
		df["EBIT_Margin"] = df["EBIT"] / df["Revenues"]
		mean_EBIT_Margin = df["EBIT_Margin"].mean()
		std_EBIT_Margin = df["EBIT_Margin"].std()

		## NWC Estimation
		df["NWC_Margin"] = df["NWC"] / df["Revenues"]
		mean_NWC_Margin = df["NWC_Margin"].mean()
		std_NWC_Margin = df["NWC_Margin"].std()
		df["change_NWC"] = df["NWC"].shift(1) - df["NWC"]


		## Growth CAPEX Estimations
		df["GCAPEX_margin"] = df["GCAPEX"] / df["Revenues"]
		mean_GCAPEX_Margin = df["GCAPEX_margin"].mean()
		std_GCAPEX_Margin = df["GCAPEX_margin"].std()

		## FCFF Estimation
		df["FCFF"] = df["EBIT"] - df["change_NWC"] - df["GCAPEX"]

		iterations = 10000
		rev_growth_dist = np.random.normal(loc = mean_change_revenue,scale = std_change_revenue, size = iterations)
		ebit_margin_dist = np.random.normal(loc = mean_EBIT_Margin,scale = std_EBIT_Margin, size = iterations)
		nwc_margin_dist = np.random.normal(loc = mean_NWC_Margin,scale = std_NWC_Margin, size = iterations)
		gcapex_margin_dist = np.random.normal(loc = mean_GCAPEX_Margin,scale = std_GCAPEX_Margin, size = iterations)


		output_distributions = []
		shares_outs = float(shares_outs)
		for i in range(iterations):
			revenue = df["Revenues"].iloc[-1]*(1+rev_growth_dist[i]) # last annual value
			ebit = df["Revenues"].iloc[-1]*(ebit_margin_dist[i])
			nwc_previous_period = df["NWC"].iloc[-2] ## Goes to the penultimo value of the dataseries
			nwc = df["Revenues"].iloc[-1]*(nwc_margin_dist[i])
			change_nwc = nwc - nwc_previous_period ## Picks the previous NWC
			gcapex = df["Revenues"].iloc[-1]*(gcapex_margin_dist[i])

			fcff = ebit -change_nwc -gcapex

			terminal_value = float((fcff*(1+0.02)/(wacc-0.02)))
			

			terminal_value_per_share = terminal_value/shares_outs



			output_distributions.append(terminal_value_per_share)

		#print(output_distributions)
		perc_25 = np.percentile(output_distributions,25)
		mean_value = np.mean(output_distributions)
		plt.hist(output_distributions, bins = iterations, density = True)
		plt.axvline(price, color='k', linestyle='dashed', linewidth=1)
		plt.show()

		#time.sleep(100)
		return (perc_25, mean_value,price)
		
		

	else:
		return (None,None,None)


dcf_valuation("AAPL")




#stock_list = ["PTON","OHI","TSLA","MSFT","FB"]


#data_symbols = pd.read_csv("nasdaq_symbols.csv")

#stock_symbols = data_symbols["Symbol"]


#stock_symbols = ["AMZN","TSLA","MSFT", "FB","RRC","OHI","BBBB","HERO","RING"]


def values():
	mean_values = []
	p25_values = []
	prices = []
	all_symbols = []

	for i in stock_symbols:
		perc_25,mean_value,price = dcf_valuation(i)
		
		#print(mean_value)
		#print(price)
		if perc_25 != None:
			all_symbols.append(i)
			mean_values.append(mean_value)
			p25_values.append(perc_25)
			prices.append(price)
			
			time.sleep(60)
		
		else:
			print("Unexistent Data for symbol {}".format(i))
			time.sleep(60)
			pass
		#print(i)
		print(all_symbols)
		print(mean_values)
		
	df = pd.DataFrame(list(zip(stock_symbols, prices,mean_values,p25_values)),columns =['Symbol', 'Price',"MeanValue","p25Value"])






	









