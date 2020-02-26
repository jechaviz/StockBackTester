import uuid
from abc import ABCMeta, abstractmethod

class Order:
    __metaclass__ = ABCMeta
    def __init__(self, order_type, open_price, quantity, entry_time,
                 stop_loss=None, take_profit=None):
        if order_type == 'buy' or order_type == 'sell':
            self.OrderType = order_type
        else:
            raise Exception('Type has to be either buy or sell')

        self.OpenPrice = open_price
        self.Quantity = quantity
        self.OpenTime = entry_time
        self.StopLoss = stop_loss
        self.TakeProfit = take_profit
        self.Ident = uuid.uuid4()
        self.ClosePrice = None
        self.CloseTime = None
        self.Profit = None
        self.ProfitPercent = None
        self.Position = "open"

    def close_order(self, close_price, close_time):
        self.ClosePrice = close_price
        self.CloseTime = close_time
        self.Position = "close"
        self.calculate_profit()

    @abstractmethod
    def calculate_profit(self):
        """
        Calculate Profit of Order
        """

    @abstractmethod
    def try_to_close(self, candle_high, candle_low, time, pre_candle_close=0.0, pre_time=None):
        """
        Try to close when TakeProfit or StopLoss hits.
        :param candle_high:
        :param candle_low:
        :param time:
        :param pre_candle_close:
        :param pre_time:
        :return: True or False
        """


class BuyOrder(Order):

    def __init__(self, open_price, quantity, open_time, stop_loss=None, take_profit=None):
        if stop_loss and stop_loss >= open_price:
            raise Exception('Stop loss trigger for buy order should be <= entry_price')
        if take_profit and take_profit <= open_price:
            raise Exception('Stop loss trigger for buy order should be >= entry_price')
        Order.__init__(self, 'buy', open_price, quantity, open_time, stop_loss, take_profit)
        print('[ID: %s] Buying %d@%f (New order)' % (self.Ident, self.Quantity, self.OpenPrice))

    def calculate_profit(self):
        if self.Position == 'close':
            self.Profit = (self.ClosePrice - self.OpenPrice) * self.Quantity
            self.ProfitPercent = (100.0 * self.Profit / self.Quantity) / self.OpenPrice
        else:
            print('WARNING: Calling calculate_profit for open order!')

    def try_to_close(self, candle_high, candle_low, time, pre_candle_close=0.0, pre_time=None):
        if self.Position == 'open':
            if self.TakeProfit != 0 and self.TakeProfit <= candle_high:
                print('[ID: %s] Target price trigger executed at candle_high %f. Closing %s...' %
                      (self.Ident, candle_high, self.OrderType))
                self.close_order(candle_high, time)
                return True
            elif self.StopLoss != 0 and self.StopLoss >= candle_low:
                print('[ID: %s] Stop loss trigger executed at candle_low %f. Closing %s...' %
                      (self.Ident, candle_low, self.OrderType))
                self.close_order(candle_low, time)
                return True
            elif self.OpenTime.date() != time.date():
                print('[ID: %s] Out Of day executed at Previous day Closing Price %f. Closing %s...' %
                      (self.Ident, pre_candle_close, self.OrderType))
                self.close_order(pre_candle_close, pre_time)
                return True
            else:
                return False
        else:
            print('Warning: Trying to close an Order which is already closed')
            return False


class SellOrder(Order):

    def __init__(self, open_price, quantity, open_time, stop_loss=None, take_profit=None):
        if stop_loss and stop_loss <= open_price:
            raise Exception('Stop loss trigger for buy order should be <= entry_price')
        if take_profit and take_profit >= open_price:
            raise Exception('Stop loss trigger for buy order should be >= entry_price')
        Order.__init__(self, 'sell', open_price, quantity, open_time, stop_loss, take_profit)
        print('[ID: %s] Selling %d@%f (New order)' % (self.Ident, self.Quantity, self.OpenPrice))

    def calculate_profit(self):
        if self.Position == 'close':
            self.Profit = (self.OpenPrice - self.ClosePrice) * self.Quantity
            self.ProfitPercent = (100.0 * self.Profit / self.Quantity) / self.OpenPrice
        else:
            print('WARNING: Calling calculate_profit for open order!')

    def try_to_close(self, candle_high, candle_low, time, pre_candle_close=0.0, pre_time=None):
        if self.Position == 'open':
            if self.TakeProfit != 0 and self.TakeProfit >= candle_low:
                print('[ID: %s] Target price trigger executed at candle_low %f. Closing %s...' %
                      (self.Ident, candle_low, self.OrderType))
                self.close_order(candle_low, time)
                return True
            elif self.StopLoss != 0 and self.StopLoss <= candle_high:
                print('[ID: %s] Stop loss trigger executed at candle_high %f. Closing %s...' %
                      (self.Ident, candle_high, self.OrderType))
                self.close_order(candle_high, time)
                return True
            elif self.OpenTime.date() != time.date():
                print('[ID: %s] Out Of day executed at Previous day Closing Price %f. Closing %s...' %
                      (self.Ident, pre_candle_close, self.OrderType))
                self.close_order(pre_candle_close, pre_time)
                return True
            else:
                return False
        else:
            print('Warning: Trying to close an Order which is already closed')
            return False
