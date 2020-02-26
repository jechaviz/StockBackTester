from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox,
        QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QSizePolicy, QTableWidgetItem,
        QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QToolButton, QFileDialog, QMessageBox)
import sys
import os
from FilterStrategy import FilterStrategy
import threading
from datetime import datetime
import time

App = QApplication(sys.argv)

OrderHeader = ["Open Time", "Stock", "Open Price", "Close Price", "Close Time", "Profit"]
Stocks = []


class WidgetGallery(QDialog):
    progressChanged = pyqtSignal(int)
    progressInited = pyqtSignal(int)

    def __init__(self, title="sample", style="windowsvista", width=1400, height=600, parent=None):
        super(WidgetGallery, self).__init__(parent, flags=Qt.WindowMinimizeButtonHint| Qt.WindowMaximizeButtonHint| Qt.WindowCloseButtonHint)

        self.resize(width, height)

        self.originalPalette = QApplication.palette()

        self.DataPathText = QLineEdit()

        styleComboBox = QComboBox()
        styleComboBox.addItems(QStyleFactory.keys())

        styleLabel = QLabel("&Style:")
        styleLabel.setBuddy(styleComboBox)

        self.useStylePaletteCheckBox = QCheckBox("&Use style's standard palette")
        self.useStylePaletteCheckBox.setChecked(True)

        disableWidgetsCheckBox = QCheckBox("&Disable widgets")

        self.createTopLeftGroupBox()
        self.createTopRightGroupBox()
        self.createBottomLeftTabWidget()
        self.createBottomRightGroupBox()
        self.createProgressBar()

        styleComboBox.activated[str].connect(self.changeStyle)
        self.useStylePaletteCheckBox.toggled.connect(self.changePalette)
        disableWidgetsCheckBox.toggled.connect(self.topLeftGroupBox.setDisabled)
        disableWidgetsCheckBox.toggled.connect(self.topRightGroupBox.setDisabled)
        disableWidgetsCheckBox.toggled.connect(self.bottomLeftTabWidget.setDisabled)
        disableWidgetsCheckBox.toggled.connect(self.bottomRightGroupBox.setDisabled)
        disableWidgetsCheckBox.toggled.connect(self.progressBarGroupBox.setDisabled)

        topLayout = QHBoxLayout()
        topLayout.addWidget(styleLabel)
        topLayout.addWidget(styleComboBox)
        topLayout.addStretch(1)
        topLayout.addWidget(self.useStylePaletteCheckBox)
        topLayout.addWidget(disableWidgetsCheckBox)

        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        mainLayout.addWidget(self.topLeftGroupBox, 1, 0)
        mainLayout.addWidget(self.topRightGroupBox, 1, 1)
        mainLayout.addWidget(self.bottomLeftTabWidget, 2, 0)
        mainLayout.addWidget(self.bottomRightGroupBox, 2, 1)
        mainLayout.addWidget(self.progressBarGroupBox, 3, 0, 3, 2)

        mainLayout.setRowStretch(1, 1)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)

        self.setWindowTitle(title)
        self.changeStyle(style)
        self.status = False
        self.progressChanged.connect(self.advanceProgressBar)
        self.progressInited.connect(self.initProgressBar)
        self.balance = 0

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        self.changePalette()

    def changePalette(self):
        if (self.useStylePaletteCheckBox.isChecked()):
            QApplication.setPalette(QApplication.style().standardPalette())
        else:
            QApplication.setPalette(self.originalPalette)

    def advanceProgressBar(self):
        curVal = self.progressBar.value()
        maxVal = self.progressBar.maximum()
        curVal += 1
        if curVal > maxVal:
            curVal = maxVal
        self.progressBar.setValue(curVal)

    def initProgressBar(self):
        self.progressBar.setValue(0)

    def open_file_dialog(self):
        directory = str(QFileDialog.getExistingDirectory())
        self.DataPathText.setText('{}'.format(directory))

    def createTopLeftGroupBox(self):
        self.topLeftGroupBox = QGroupBox("Initial Settings")

        directoryLayout = QHBoxLayout()
        directoryLabel = QLabel("Data Path:       ")
        toolButtonOpenDialog = QToolButton()
        toolButtonOpenDialog.setObjectName("toolButtonOpenDialog")
        toolButtonOpenDialog.clicked.connect(self.open_file_dialog)
        toolButtonOpenDialog.setText("...")

        directoryLayout.addWidget(directoryLabel)
        directoryLayout.addWidget(self.DataPathText)
        directoryLayout.addWidget(toolButtonOpenDialog)

        initLayout = QHBoxLayout()
        self.InitialAmountText = QLineEdit("10000")
        initialAmountLabel = QLabel("Initial Amount: ")
        initLayout.addWidget(initialAmountLabel)
        initLayout.addWidget(self.InitialAmountText)

        buyRuleLayout = QHBoxLayout()
        buyRuleText = QTextEdit()
        buyRuleText.setPlainText("Buy Rule:\n"
                              " 1. If all Filters are met then place a buy order at the price that existed when all filter where meet. Buy will 100% of avalable funds \n"
                              " 2. Never buy the same company's stock more than 1 time in a single day.\n")
        buyRuleText.setDisabled(True)
        buyRuleLayout.addWidget(buyRuleText)

        sellRuleLayout = QHBoxLayout()
        sellRuleText = QTextEdit()
        sellRuleText.setPlainText("Sell Rule:\n"
                                 "  1. After the stocks have been purchased then place the sell order at (the buyprice pluse Sell Condition percent)")
        sellRuleText.setDisabled(True)
        sellRuleLayout.addWidget(sellRuleText)

        layout = QVBoxLayout()
        layout.addLayout(directoryLayout)
        layout.addLayout(initLayout)
        layout.addLayout(buyRuleLayout)
        layout.addLayout(sellRuleLayout)
        layout.addStretch(1)
        self.topLeftGroupBox.setLayout(layout)

    def createTopRightGroupBox(self):
        self.topRightGroupBox = QGroupBox("Filters")

        minMarketCapLayout = QHBoxLayout()
        minMarketCapLabel = QLabel("Minimum Market Capitalization:                                          ")
        self.MinMarketCapText = QLineEdit("1000000")
        minMarketCapLayout.addWidget(minMarketCapLabel)
        minMarketCapLayout.addWidget(self.MinMarketCapText)

        minRisenLayout = QHBoxLayout()
        self.MinRisenText = QLineEdit("20")
        minRisenLabel = QLabel("Minimum % Price Has Risen Since Previous Closing Price: ")
        minRisenLayout.addWidget(minRisenLabel)
        minRisenLayout.addWidget(self.MinRisenText)

        minSlopeLayout = QHBoxLayout()
        self.MinSlopeText = QLineEdit("0.1")
        minSlopeLabel = QLabel("Minimum Slope Acceptable:                                                ")
        minSlopeLayout.addWidget(minSlopeLabel)
        minSlopeLayout.addWidget(self.MinSlopeText)

        sellConditionLayout = QHBoxLayout()
        self.SellConditionText = QLineEdit("0.75")
        sellConditionLabel = QLabel("To Sell When the Buy price plus this Percent (%):            ")
        sellConditionLayout.addWidget(sellConditionLabel)
        sellConditionLayout.addWidget(self.SellConditionText)

        layout = QVBoxLayout()
        layout.addLayout(minMarketCapLayout)
        layout.addLayout(minRisenLayout)
        layout.addLayout(minSlopeLayout)
        layout.addLayout(sellConditionLayout)
        layout.addStretch(1)

        self.topRightGroupBox.setLayout(layout)

    def createBottomLeftTabWidget(self):
        self.bottomLeftTabWidget = QTabWidget()
        self.bottomLeftTabWidget.setSizePolicy(QSizePolicy.Preferred,
                QSizePolicy.Ignored)

        tab1 = QWidget()
        self.OrderTable = CustomTableWidget()
        self.OrderTable.setColumnCount(6)
        self.OrderTable.setHorizontalHeaderLabels(OrderHeader)
        #self.OrderTable.setSortingEnabled(True)

        #self.OrderTable.set_row(("3434", "4454", "54545", "2323", "12"))
        #self.OrderTable.resizeColumnsToContents()

        tab1hbox = QHBoxLayout()
        tab1hbox.setContentsMargins(5, 5, 5, 5)
        tab1hbox.addWidget(self.OrderTable)
        tab1.setLayout(tab1hbox)
        self.bottomLeftTabWidget.addTab(tab1, "&Orders")

    def createBottomRightGroupBox(self):
        self.bottomRightGroupBox = QGroupBox("Result")

        balanceLayout = QHBoxLayout()
        balanceLabel = QLabel("Balance:               ")
        self.BalanceText = QLineEdit(self.InitialAmountText.text())
        balanceLayout.addWidget(balanceLabel)
        balanceLayout.addWidget(self.BalanceText)
        self.BalanceText.setDisabled(True)

        totalOrdersLayout = QHBoxLayout()
        totalOrdersLabel = QLabel("Total Orders:        ")
        self.TotalOrders = QLineEdit("0")
        totalOrdersLayout.addWidget(totalOrdersLabel)
        totalOrdersLayout.addWidget(self.TotalOrders)
        self.TotalOrders.setDisabled(True)

        profitOrdersLayout = QHBoxLayout()
        profitOrdersLabel = QLabel("Profit Orders:       ")
        self.ProfitOrders = QLineEdit("0")
        profitOrdersLayout.addWidget(profitOrdersLabel)
        profitOrdersLayout.addWidget(self.ProfitOrders)
        self.ProfitOrders.setDisabled(True)

        lossOrdersLayout = QHBoxLayout()
        lossOrdersLabel = QLabel("Loss Orders:         ")
        self.LossOrders = QLineEdit("0")
        lossOrdersLayout.addWidget(lossOrdersLabel)
        lossOrdersLayout.addWidget(self.LossOrders)
        self.LossOrders.setDisabled(True)

        profitPercentLayout = QHBoxLayout()
        profitPercentLabel = QLabel("Profit Orders(%): ")
        self.ProfitPercentText = QLineEdit("0.0")
        profitPercentLayout.addWidget(profitPercentLabel)
        profitPercentLayout.addWidget(self.ProfitPercentText)
        self.ProfitPercentText.setDisabled(True)

        lossPercentLayout = QHBoxLayout()
        lossPercentLabel = QLabel("Loss Orders(%):   ")
        self.LossPercentText = QLineEdit("0.0")
        lossPercentLayout.addWidget(lossPercentLabel)
        lossPercentLayout.addWidget(self.LossPercentText)
        self.LossPercentText.setDisabled(True)

        profitsLayout = QHBoxLayout()
        profitsLabel = QLabel("Total Profit($):      ")
        self.ProfitText = QLineEdit("0.0")
        profitsLayout.addWidget(profitsLabel)
        profitsLayout.addWidget(self.ProfitText)
        self.ProfitText.setDisabled(True)

        layout = QVBoxLayout()
        layout.addLayout(balanceLayout)
        layout.addLayout(totalOrdersLayout)
        layout.addLayout(profitOrdersLayout)
        layout.addLayout(lossOrdersLayout)
        layout.addLayout(profitPercentLayout)
        layout.addLayout(lossPercentLayout)
        layout.addLayout(profitsLayout)
        layout.addStretch(1)
        self.bottomRightGroupBox.setLayout(layout)

    def createProgressBar(self):
        self.progressBarGroupBox = QGroupBox()
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.startStopButton = QPushButton("Start")
        self.startStopButton.clicked.connect(self.start)
        self.progressLayout = QHBoxLayout()
        self.progressLayout.addWidget(self.progressBar)
        self.progressLayout.addWidget(self.startStopButton)
        self.progressBarGroupBox.setLayout(self.progressLayout)

    def start(self):
        if self.status is True:
            self.startStopButton.setDisabled(True)
            self.status = False
            return
        dir = self.DataPathText.text()
        if dir is None or dir == "":
            self.alarm("Please select Data path Directory!")
            return
        self.progressBar.setValue(0)
        self.OrderTable.clearContents()
        self.OrderTable.setRowCount(0)
        BackTester = self.BackTesterThread("BackTester", self)
        BackTester.start()

    def run(self):
        self.show()
        sys.exit(App.exec_())

    def alarm(self, text):
        alert = QMessageBox()
        alert.setText(text)
        alert.exec_()

    def load_stocks(self):
        if len(Stocks) > 0:
            for pip in Stocks:
                pip.initialize()
            return True

        dir = self.DataPathText.text()
        if dir is None or dir == "":
            print("Please select Data Path!")
            return False
        stock_counts = len(os.listdir(dir))
        self.progressBar.setMaximum(stock_counts)
        index = 0
        self.status = True
        self.startStopButton.setText("Loading")
        for file_name in os.listdir(dir):
            try:
                if self.status is False:
                    self.startStopButton.setDisabled(False)
                    self.startStopButton.setText("Start")
                    Stocks.clear()
                    return False

                file_path = str(dir + '\\' + file_name)
                back_tester = FilterStrategy(0, float(self.MinMarketCapText.text()),
                                             float(self.MinRisenText.text()),
                                             float(self.MinSlopeText.text()),
                                             float(self.SellConditionText.text()))

                if back_tester.read_data(file_path, file_name) is False:
                    index += 1
                    self.progressChanged.emit(index)
                    continue
                Stocks.append(back_tester)
            except Exception as e:
                print(str(e))
            index += 1
            self.progressChanged.emit(index)
        self.startStopButton.setText("Stop")
        return True

    def select_stock(self):
        count = len(Stocks)
        if count <= 0:
            return -1
        min_time = datetime.now()
        result = -1
        for i in range(count):
            if Stocks[i].Index >= Stocks[i].Amount:
                continue

            if min_time > Stocks[i].get_current_time():
                min_time = Stocks[i].get_current_time()
                result = i
        return result

    def thread_start(self):
        try:
            self.balance = float(self.InitialAmountText.text())
            self.BalanceText.setText(str(self.balance))
            self.TotalOrders.setText("0")
            self.ProfitOrders.setText("0")
            self.LossOrders.setText("0")
            self.ProfitPercentText.setText("0.0")
            self.LossPercentText.setText("0.0")
            self.ProfitText.setText("0.0")
            totalOrders = 0
            profitOrders = 0
            lossOrders = 0
            profit = 0.0
            quotes = 0
            self.status = True
            self.startStopButton.setText("Stop")
            if self.load_stocks() is False:
                self.startStopButton.setDisabled(False)
                self.status = False
                self.startStopButton.setText("Start")
                return
            if len(Stocks) is 0:
                self.startStopButton.setDisabled(False)
                self.status = False
                self.startStopButton.setText("Start")
                return
            for pip in Stocks:
                quotes += pip.Amount
            self.progressBar.setMaximum(quotes)
            index = 0
            while True:
                if self.status is False:
                    self.startStopButton.setDisabled(False)
                    self.startStopButton.setText("Start")
                    return
                if self.balance <= 0:
                    print("Initial Balance is not enough!")
                    self.status = False
                    self.startStopButton.setDisabled(False)
                    self.startStopButton.setText("Start")
                    return
                if index >= quotes:
                    print("Finished!")
                    self.status = False
                    self.startStopButton.setDisabled(False)
                    self.startStopButton.setText("Start")
                    return
                stock_num = self.select_stock()
                if stock_num < 0:
                    print("Finished!")
                    self.status = False
                    self.startStopButton.setDisabled(False)
                    self.startStopButton.setText("Start")
                    return
                try:
                    back_tester = Stocks[stock_num]
                    self.balance = back_tester.back_test(self.balance)
                    for pip in back_tester.ClosedOrders:
                        row = (pip.OpenTime.strftime('%m/%d/%Y %H:%M'), back_tester.Symbol, str(pip.OpenPrice),
                               str(pip.ClosePrice), pip.CloseTime.strftime('%m/%d/%Y %H:%M'), str(round(pip.Profit, 2)))
                        self.OrderTable.set_row(row)
                        time.sleep(0)
                    balance = self.balance
                    totalOrders += back_tester.TotalOrdersCount
                    profitOrders += back_tester.WinOrdersCount
                    lossOrders += back_tester.LossOrdersCount
                    profit += back_tester.TotalProfit

                    self.BalanceText.setText(str(round(balance, 2)))
                    self.TotalOrders.setText(str(totalOrders))
                    self.ProfitOrders.setText(str(profitOrders))
                    self.LossOrders.setText(str(lossOrders))
                    self.ProfitText.setText(str(round(profit, 2)))

                    if totalOrders is 0:
                        self.ProfitPercentText.setText("0")
                        self.LossPercentText.setText("0")
                        index += 1
                        self.progressChanged.emit(index)
                        time.sleep(0)
                        continue
                    self.ProfitPercentText.setText(
                        str(round(float(profitOrders) / float(totalOrders) * 100.0, 2)))
                    self.LossPercentText.setText(
                        str(round(float(lossOrders) / float(totalOrders) * 100.0, 2)))
                except Exception as e:
                    print(str(e))
                index += 1
                self.progressChanged.emit(index)
                time.sleep(0)
                continue
        except Exception as e:
            print(str(e))
        self.startStopButton.setDisabled(False)
        self.status = False
        self.startStopButton.setText("Start")

    class BackTesterThread(threading.Thread):
        def __init__(self, name, server):
            threading.Thread.__init__(self)
            self.name = name
            self.server = server

        def run(self):
            print("Starting " + self.name)
            self.server.thread_start()

class CustomTableWidget(QTableWidget):
    def set_row(self, row):
        try:
            index = 0
            rows = self.rowCount()
            self.setRowCount(rows+1)
            for pip in list(row):
                self.setItem(rows, index, self.createItem(pip, Qt.ItemIsSelectable | Qt.ItemIsEnabled))
                index += 1
        except Exception as e:
            print(str(e))

    def createItem(self, text, flags):
        tableWidgetItem = QTableWidgetItem(text)
        tableWidgetItem.setFlags(flags)
        return tableWidgetItem



