class BinOption(object):
    def __init__(self,S0,u,d,r):
        self.__S0 = float(S0)
        self.__u = float(u)
        self.__d = float(d)
        self.__r = float(r)
        self.__isArbitrage()
        
    def S(self,t, i):
        return self.__S0*( (1+self.__u) ** i) * ( (1 + self.__d)**(t - i) )
    def riskNeutral(self):
        return (self.__r-self.__d)/(self.__u -self.__d)
    def getRate(self):
        return self.__r       
    def __isArbitrage(self):
        if(self.__r>=self.__u or self.__r <= self.__d): print 'There is arbitrage opportunity'
        else: print 'There is no arbitrage to make'
        
class AmericanOption(object):
    def __init__(self,t):
        self.__t = int(t)
    def setT(self, t): # T for t dates
        self.__t = int(t)
    def getT(self):
        return self.__t
        
    def payOff(self, St):
        raise NotImplementedError
        
    def pricing(self, option):
        assert isinstance(option, BinOption), "Can not price non-instance of BinOption"
        q = option.riskNeutral()
        print q
        path = [0 for i in xrange(self.__t+1)]
        intermediateValue = 0.00
        
        for i in xrange(self.__t +1):
            path[i] = self.payOff(option.S(self.__t,i))
            
        for n in xrange(self.__t-1 , -1, -1):
            for i in xrange(self.__t):
                intermediateValue = ( q*path[i+1] + (1-q)*path[i] ) / (1+option.getRate())
                path[i] = self.payOff(option.S(n, i))             
                if intermediateValue > path[i]: 
                    path[i] = intermediateValue
        return round(path[0],2)
                  
class Call(AmericanOption):
    def __init__(self,t):
        AmericanOption.__init__(self,t)
    def setK(self,K): # strike price at time T or denote F as in class
        self.__K = K
    def payOff(self,St):
        if (St>self.__K): return St - self.__K
        else: return 0.0

class Put(AmericanOption):
    def __init__(self,t):
        AmericanOption.__init__(self,t)
    def setK(self,K): # strike price at time T or denote F as in class
        self.__K = K
    def payOff(self,St):
        if (St<self.__K): return self.__K - St
        else: return 0.0   
