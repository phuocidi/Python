from nlib import *
import pickle
from sys import argv
import datetime
import glob
from matplotlib import style
from matplotlib import patches as mpatches
style.use('ggplot')

class Brokerage(MCEngine):
        def __init__(self):
                self._data = pickle.load(open(argv[1]))
                self._tdays = int(argv[2])
                self._ci = int(argv[3])
                self._db = {} #database
                self._df = None
                self._broker_portfolio = {}
                self._df_client_var = {}
                self._df_broker_var ={}
		self._stock_path = {}
                self._seed = random.random() # generate random seed for 1 run
                self.__loadData()


        def __loadData(self):
		'''
		Create a pickle database. If database existed, it will load to RAM. Otherwise, it will download historial data from yahoo, 
		load the data to new database and dumb to disk.
		'''
                bStocks=[]
                dbName = "database.pickle"
                for stocks in self._data.values():
                        for stock in stocks.keys():
                                if stock not in bStocks:
                                        bStocks.append(stock)
                                        self._broker_portfolio[stock] = stocks[stock]
                                else: # update brokerPorfolio
                                        value = self._broker_portfolio[stock] + stocks[stock]
                                        self._broker_portfolio[stock] = value
                                        

                if glob.glob(dbName):
                        self._db = pickle.load(open(dbName))
                else:
                        toRemove=[]
                        for symbol in bStocks:
                                if symbol not in self._db:
                                        days = YStock(symbol).historical()
                                        if len(days)>0:
                                                self._db[symbol] = days
                                        else:
                                                toRemove.append(symbol)
                        #clean out BKG.R and WAG
                        for symbol in toRemove:
                                bStocks.remove(symbol)
                                
                        pickle.dump(self._db,open(dbName,'w'))

        def simulate_once(self):
		'''
		Generate return for one porfolio at a time.  
	
		'''
                path = [random.randint(0,250-1) for day in range(self._tdays)]
                portfolio_return = []
                for symbol, amount in self.portfolio.items(): # self.portfolio will be generated within function process
                        if symbol in self._db:
                                days = self._db[symbol][-250:]
                                historical_data = [days[i] for i in path]
                                log_returns = [day['log_return'] for day in historical_data]
                                tdays_log_returns = sum(log_returns)
                                today_price = days[-1]['close']
                                tdays_price = today_price*exp(tdays_log_returns)
                                portfolio_return.append((tdays_price-today_price)*amount)

				# extra work to plot
				if symbol not in self._stock_path:
					self._stock_path[symbol] = log_returns
                return sum(portfolio_return)


	def showPlot(self):
		'''
		Helper function. Creating simulation price
		'''
		for symbol in self._stock_path.keys():
			try:
				data_historical = []
				days = self._db[symbol][-250:]
				for i,day in enumerate(days):
					data_historical.append( (i, day['close'] ))

				today_close = data_historical[-1][1]
				index = len(data_historical)
				data_future = [(index-1,today_close)]
				for log_return in self._stock_path[symbol]:
					next_day_close = today_close * exp(log_return)
					data_future.append( (index,next_day_close) )
					today_close = next_day_close
					index += 1
			
				canvas = Canvas(xlab= "Date", ylab="Price",title = 'MC Simulation')
				pastPatch = mpatches.Patch(color ='blue',label = 'Past Price' )
				futurePatch = mpatches.Patch(color = 'red', label = 'Simulation Price')
				canvas.plot(data_historical, color= 'blue').plot(data_future, color = 'red')
				canvas.legend = [(pastPatch,'Past price' ) , (futurePatch,'Simulation price') ]
				if not os.path.exists('path'): os.mkdir('path')
				canvas.save('path/%ssim.png' % symbol)
			except:
				print "ERROR! The sticker you requested is not available"	

	def showHist(self,data,var, name):
		'''
		helper function: create histogram
		params: 
		- data: a list of data
		- var : value at risk of that data
		- name: sticker of the stock
		'''
		fullPatch = mpatches.Patch(color ='red')
		VaRPatch = mpatches.Patch(color = 'blue')
		canvas = Canvas(xlab='Returns', ylab='Frequency',title= name + ' Distribution')
		canvas.hist(data,color = 'red')
		canvas.hist(data[:data.index(var)], color = 'blue')
		canvas.legend = [(fullPatch,'Full distribution' ),(VaRPatch,'VaR distribution' )]
		if not os.path.exists('hist'): os.mkdir('hist')
		canvas.save('hist/%s_distribution.png' % name)

        def __update_simulate(self,portfolio):
        	"""
        	For each client, it retrieve  the porfolio, make the portfolio available for simulate_once
        	each client will have the same seed so that the day index in each simulate_once
        	is similar, and each call in simulate_many will have different day path within each
        	client's portfolio. 
		
		params:
		- portfolio: a dictionary of stock and amount of each client.
        	"""
                random.seed(self._seed)
                self.portfolio = portfolio
                self.simulate_many()
                del self.portfolio


        def process(self):
		'''
		Calculate value at risk for each client, and brokerage.
		print the VaR of each client and brokerage to the screen
		Write the data frame of value at risk as csv file to disk
		'''
                import pandas as pd
		
                for client, portfolio in self._data.items():
                        self.__update_simulate(portfolio)
                        self._df_client_var[client] = self.var(100 - int(self._ci))
			# Comment out to use helper function
			self.showHist(self.results,  self._df_client_var[client], client)

                self.__update_simulate(self._broker_portfolio)
                self._df_broker_var['cumulative'] = self.var(100 - int(self._ci))
		# Comment out to use helper function	
		self.showHist(self.results, self._df_broker_var['cumulative'],'Cumulative' )

                for client, var in self._df_client_var.items():
                        print client, var
                for b, var in self._df_broker_var.items():
                        print b, var
		total_clients = len(self._df_client_var.keys())  
                indexes = [i for i in range(total_clients) ]
                client_df = pd.DataFrame(self._df_client_var.items(), columns =['Name','Value at risk'], index = indexes)
		broker_df = pd.DataFrame(self._df_broker_var.items(),columns =['Name','Value at risk'],index = [total_clients]) 
		self._df = pd.concat([client_df,broker_df])
                self._df.to_csv('log_VAR.csv', sep = ',', encoding ='utf-8')
                

broker = Brokerage()  
broker.process()
broker.showPlot()

