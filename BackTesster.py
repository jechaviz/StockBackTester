from abc import ABCMeta, abstractmethod
from Order import BuyOrder, SellOrder


class BackTester:
    __metaclass__ = ABCMeta

    def __init__(self, balance=0):
        self.Symbol = None
        self.TimeLines = []
        self.OpenPrices = []
        self.ClosePrices = []
        self.HighPrices = []
        self.LowPrices = []
        self.Volumes = []
        self.TimeDecimals = []
        self.OpenOrders = []
        self.ClosedOrders = []
        self.TotalProfit = 0.0
        self.TotalOrdersCount = 0
        self.TotalProfitPercent = 0.0
        self.LossOrdersCount = 0
        self.WinOrdersCount = 0
        self.Balance = balance

    @abstractmethod
    def read_data(self, file_path):
        """
        Implement this method to read input data into 2 variables -
        1. timeline
        2. datapoints
        """

    def buy_trade(self, open_price, quantity, open_time, stop_loss=None, take_profit=None, balance=0):
        if self.Balance < 0:
            return False
        buy_order = BuyOrder(open_price, quantity, open_time, stop_loss, take_profit)
        self.Balance -= open_price * quantity
        self.OpenOrders.append(buy_order)
        return True

    def sell_trade(self, open_price, quantity, open_time, stop_loss=None, take_profit=None, balance=0):
        sell_order = SellOrder(open_price, quantity, open_time, stop_loss, take_profit)
        self.Balance += open_price * quantity
        self.OpenOrders.append(sell_order)
        return True

    def close_trade(self, order, balance=0):
        if order.OrderType == "buy":
            self.Balance += order.ClosePrice * order.Quantity
        elif order.OrderType == "sell":
            self.Balance -= order.ClosePrice * order.Quantity
        else:
            return False
        self.TotalProfit += order.Profit
        self.TotalOrdersCount += 1
        self.TotalProfitPercent += order.ProfitPercent
        if order.Profit < 0:
            self.LossOrdersCount += 1
        else:
            self.WinOrdersCount += 1
        self.ClosedOrders.append(order)
        return True

    @abstractmethod
    def strategy(self, index, balance=0):
        """
        open order according to strategy
        :param index: candle number
        :param balance: Balance
        """

    def back_test(self, balance=0):
        for i in range(len(self.OpenPrices)):
            j = 0
            while j < len(self.OpenOrders):
                if self.OpenOrders[j].try_to_close(self.HighPrices[i], self.LowPrices[i], self.TimeLines[i],
                                                   self.ClosePrices[i - 1], self.TimeLines[i - 1]) is False:
                    j += 1
                    continue
                self.close_trade(self.OpenOrders.pop(j))
            self.strategy(i)
            if i >= len(self.OpenPrices) - 1 or self.Balance < 0:
                k = 0
                while k < len(self.OpenOrders):
                    print(str(self.OpenOrders[k].Ident) + " Order was closed by Limited Timeline. OrderType: "
                          + self.OpenOrders[k].OrderType)
                    self.OpenOrders[k].close_order(self.ClosePrices[i], self.TimeLines[i])
                    self.close_trade(self.OpenOrders.pop(k))
                return
