from BackTesster import BackTester
from datetime import datetime
from pandas_datareader import data
import numpy as np
from datetime import timedelta
from Order import BuyOrder, SellOrder


class FilterStrategy(BackTester):
    def __init__(self, balance=0, min_market_cap=100000.0, min_risen=20.0, min_slope=0.1, stop_cond=0.75, quantity=1):
        super(FilterStrategy, self).__init__(balance)
        self.MinMarketCap = min_market_cap
        self.MinRisen = min_risen
        self.MinSlope = min_slope / 100.0
        self.Min15Slope = min_slope / 100.0
        self.Min30Slope = min_slope / 100.0
        self.StopCond = stop_cond
        self.MarketCap = 0.0
        self.Quantity = quantity
        self.Amount = 0
        self.Index = 0

    def read_data(self, file_path, file_name=""):
        try:
            self.Symbol = file_name.split('.')[0]
            self.MarketCap = self.get_market_cap()
            if self.MarketCap < self.MinMarketCap:
                print(self.Symbol + " stock's Market capitalization(" + str(self.MarketCap)
                      + ") is less than Minimum Market capitalization(" + str(self.MinMarketCap) + ").")
                return False
            file = open(file_path, "r")
            lines = file.readlines()
            for line in lines:
                sep = line.split(',')
                if len(sep) < 7:
                    continue
                time = sep[0] + " " + sep[1]
                self.TimeLines.append(datetime.strptime(time, '%m/%d/%Y %H:%M'))
                hm = sep[1].split(':')
                hour = float(hm[0]) + float(hm[1]) / 60.0
                self.TimeDecimals.append(hour)
                self.OpenPrices.append(float(sep[2]))
                self.HighPrices.append(float(sep[3]))
                self.LowPrices.append(float(sep[4]))
                self.ClosePrices.append(float(sep[5]))
                self.Volumes.append(float(sep[6]))
            file.close()
            self.Amount = len(self.OpenPrices)
            return True
        except Exception as e:
            print(str(e))
            return False

    def back_test(self, balance=0):
        self.TotalProfit = 0
        self.TotalOrdersCount = 0
        self.TotalProfitPercent = 0
        self.LossOrdersCount = 0
        self.WinOrdersCount = 0
        self.ClosedOrders.clear()
        if self.Index >= self.Amount:
            return balance
        j = 0
        while j < len(self.OpenOrders):
            if self.OpenOrders[j].try_to_close(self.HighPrices[self.Index], self.LowPrices[self.Index],
                                               self.TimeLines[self.Index], self.ClosePrices[self.Index - 1],
                                               self.TimeLines[self.Index - 1]) is False:
                j += 1
                continue
            balance = self.close_trade(self.OpenOrders.pop(j), balance)
        balance = self.strategy(self.Index, balance)
        if self.Index >= len(self.OpenPrices) - 1 or balance < 0:
            k = 0
            while k < len(self.OpenOrders):
                print(str(self.OpenOrders[k].Ident) + " Order was closed by Limited Timeline. OrderType: "
                      + self.OpenOrders[k].OrderType)
                self.OpenOrders[k].close_order(self.ClosePrices[self.Index], self.TimeLines[self.Index])
                balance = self.close_trade(self.OpenOrders.pop(k), balance)
        self.Index += 1
        return balance

    def strategy(self, index, balance=0):
        try:
            if self.check_orders_today(index) is False:
                return balance
            pre_closed = self.get_closed_price(index)

            if self.filter_min_risen(index, pre_closed, 1) is False or self.filter_min_slope(index, pre_closed, 1) is False:
                return balance
            pips = self.HighPrices[index] * self.StopCond / 100.0
            #stop_loss = self.HighPrices[index] - pips
            take_profit = self.HighPrices[index] + pips
            balance = self.buy_trade(self.HighPrices[index], self.Quantity, self.TimeLines[index], 0,
                                     take_profit, balance)
            return balance
        except Exception as e:
            print(str(e))
            return balance

    def filter_min_risen(self, index, pre_closed, applied=0):
        try:
            if pre_closed <= 0:
                return False
            if applied == 0:
                min_risen = pre_closed * self.MinRisen / 100.0
                if pre_closed + min_risen > self.OpenPrices[index]:
                    return False
                return True
            elif applied == 1:
                min_risen = pre_closed * self.MinRisen / 100.0
                if pre_closed + min_risen > self.HighPrices[index]:
                    return False
                return True
            elif applied == 2:
                min_risen = pre_closed * self.MinRisen / 100.0
                if pre_closed + min_risen > self.LowPrices[index]:
                    return False
                return True
            elif applied == 3:
                min_risen = pre_closed * self.MinRisen / 100.0
                if pre_closed + min_risen > self.ClosePrices[index]:
                    return False
                return True
            return False
        except Exception as e:
            print(str(e))
            return False

    def filter_min_slope(self, index, pre_closed, applied=0):
        try:
            if index <= 0:
                return False
            today_first = self.get_today_first_index(index)
            today_slope, today_inter = self.calculate_slope(today_first, index, pre_closed, applied)
            if today_slope < self.MinSlope:
                return False
            m30_index = self.get_today_delta_index(index, today_first, timedelta(minutes=30))
            m30_slope, m30_inter = self.calculate_slope(m30_index, index, pre_closed, applied)
            if m30_slope < self.Min30Slope:
                return False
            m15_index = self.get_today_delta_index(index, today_first, timedelta(minutes=15))
            m15_slope, m15_inter = self.calculate_slope(m15_index, index, pre_closed, applied)
            if m15_slope < self.Min15Slope:
                return False
            return True
        except Exception as e:
            print(str(e))
            return False

    def get_market_cap(self):
        try:
            market_cap = data.get_quote_yahoo(self.Symbol)['marketCap']
            return market_cap.values[0]
        except Exception as e:
            print(str(e))
            return 0.0

    def get_closed_price(self, index):
        try:
            current = self.TimeLines[index]
            cur_date = current.date()
            for i in range(index-1, -1, -1):
                pre = self.TimeLines[i].date()
                if pre == cur_date:
                    continue
                return self.ClosePrices[i]
            return self.ClosePrices[0]
        except Exception as e:
            print(str(e))
            return -1

    def get_today_first_index(self, index):
        try:
            cur_date = self.TimeLines[index].date()
            for i in range(index - 1, -1, -1):
                pre = self.TimeLines[i].date()
                if pre == cur_date:
                    continue
                return i + 1
            return 0
        except Exception as e:
            print(str(e))
            return index

    def get_today_delta_index(self, index, first_index, delta):
        try:
            pre_date = self.TimeLines[index] - delta

            for i in range(index - 1, first_index - 1, -1):
                if self.TimeLines[i] >= pre_date:
                    continue
                return i + 1
            return 0
        except Exception as e:
            print(str(e))
            return index

    def check_orders_today(self, index):
        cur_date = self.TimeLines[index].date()
        for pip in self.OpenOrders:
            if pip.OpenTime.date() == cur_date:
                return False
        for i in range(len(self.ClosedOrders) - 1, -1, -1):
            if self.ClosedOrders[i].OpenTime.date() == cur_date:
                return False
            return True
        return True

    def calculate_slope(self, begin, end, pre_close, applied=0):
        try:
            x = self.TimeDecimals[begin:end + 1]
            prices = self.OpenPrices
            if applied == 1:
                prices = self.HighPrices
            elif applied == 2:
                prices = self.LowPrices
            elif applied == 3:
                prices = self.ClosePrices
            y = [((prices[t] - pre_close) / pre_close) for t in range(begin, end + 1)]
            slope, intercept = np.polyfit(x, y, 1)
            return slope, intercept
        except Exception as e:
            print(str(e))
            return 0

    def buy_trade(self, open_price, quantity, open_time, stop_loss=None, take_profit=None, balance=0):
        if balance < 0:
            return balance
        buy_order = BuyOrder(open_price, quantity, open_time, stop_loss, take_profit)
        balance -= open_price * quantity
        self.OpenOrders.append(buy_order)
        return balance

    def sell_trade(self, open_price, quantity, open_time, stop_loss=None, take_profit=None, balance=0):
        sell_order = SellOrder(open_price, quantity, open_time, stop_loss, take_profit)
        balance += open_price * quantity
        self.OpenOrders.append(sell_order)
        return balance

    def close_trade(self, order, balance=0):
        if order.OrderType == "buy":
            balance += order.ClosePrice * order.Quantity
        elif order.OrderType == "sell":
            balance -= order.ClosePrice * order.Quantity
        else:
            return balance
        self.TotalProfit = order.Profit
        self.TotalOrdersCount = 1
        self.TotalProfitPercent = order.ProfitPercent
        if order.Profit < 0:
            self.LossOrdersCount = 1
        else:
            self.WinOrdersCount = 1
        #self.ClosedOrders.clear()
        self.ClosedOrders.append(order)
        return balance

    def get_current_time(self):
        return self.TimeLines[self.Index]

    def initialize(self):
        self.Index = 0
        self.TotalProfit = 0
        self.TotalOrdersCount = 0
        self.TotalProfitPercent = 0
        self.ClosedOrders.clear()
        self.OpenOrders.clear()
        self.LossOrdersCount = 0
        self.WinOrdersCount = 0
