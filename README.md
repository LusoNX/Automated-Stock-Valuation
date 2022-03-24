# Automated-Stock-Valuation
Output of a standardized report for stock valuation, using Dividend Discount Model (DDM), Discounted Cash Flow (DCF) and PEER Evaluation

** Notice **
This is by no means an approach to value companies, only a structured script that employs some of the common valuations used in traditional finance. Even though the results are somewhat useful if you are evaluating mature companies or companies with a predictable stream of cash flows (such as REITS), the results lack meaning when applied to growth companies or companies with unpredictable cash flows. 

After defining your directory, run the script "doc_reader" to produce an automated valuation.
Details of the DCF and DDM assumptions used for the estimations are shown in the document.
Peer evaluation is made on both industry and sector provided in by finance yahoo (using yfinance.py library).
The Monte Carlo Simulation is made by normalizing each input factor (such as revenue growth rate, ebit margin, net working capital to Revenue and Growth CAPEX to Revenue) 
The output looks something like this (ugly i know).

[OHI.Summary.docx](https://github.com/LusoNX/Automated-Stock-Valuation/files/8345978/OHI.Summary.docx)

