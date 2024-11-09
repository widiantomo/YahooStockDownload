import sys
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib
import webbrowser
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from datetime import datetime

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize an empty DataFrame for self.df and for news data
        self.df = pd.DataFrame()
        self.news_df = pd.DataFrame()  # DataFrame to hold news date, polarity, and content information

        # Canvas for plotting
        self.sc = MplCanvas(self, width=10, height=8, dpi=100)

        # Create toolbar
        toolbar = NavigationToolbar(self.sc, self)

        # DateTime widgets for start and end date
        self.start_date = QtWidgets.QDateTimeEdit(self)
        self.start_date.setCalendarPopup(True)
        self.start_date.setDateTime(QtCore.QDateTime.currentDateTime().addDays(-7))  # Default to 7 days ago
        
        self.end_date = QtWidgets.QDateTimeEdit(self)
        self.end_date.setCalendarPopup(True)
        self.end_date.setDateTime(QtCore.QDateTime.currentDateTime())  # Default to current date and time

        # Symbol selector combo box
        self.symbol_selector = QtWidgets.QComboBox(self)
        self.symbol_selector.addItems(self.fetch_symbols())  # Populate with symbols from the database
        self.symbol_selector.currentIndexChanged.connect(self.update_plot)  # Update plot on symbol change

        # Load Data button
        load_data_button = QtWidgets.QPushButton("Load Data")
        load_data_button.clicked.connect(self.update_plot)  # Connect button click to update plot

        # Text box to display news content
        self.news_text_box = QtWidgets.QTextEdit(self)
        self.news_text_box.setReadOnly(True)
        self.news_text_box.setPlaceholderText("Click on a news marker to see the news content.")

        # Set font size for the text box
        font = self.news_text_box.font()
        font.setPointSize(16)  # Set font size to 16
        self.news_text_box.setFont(font)

        # Label to display hyperlink
        self.news_link_label = QtWidgets.QLabel(self)
        self.news_link_label.setTextFormat(QtCore.Qt.RichText)
        self.news_link_label.setOpenExternalLinks(False)  # Disable automatic opening to handle it ourselves
        self.news_link_label.linkActivated.connect(self.open_link)  # Connect link activation to open_link method

        # Left layout for toolbar, chart, symbol selector, date selectors, and load data button
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(toolbar)
        left_layout.addWidget(self.sc)
        left_layout.addWidget(QtWidgets.QLabel("Symbol:"))
        left_layout.addWidget(self.symbol_selector)  # Add symbol selector
        left_layout.addWidget(QtWidgets.QLabel("Start Date:"))
        left_layout.addWidget(self.start_date)
        left_layout.addWidget(QtWidgets.QLabel("End Date:"))
        left_layout.addWidget(self.end_date)
        left_layout.addWidget(load_data_button)  # Add Load Data button

        # Right layout for news content and hyperlink
        news_layout = QtWidgets.QVBoxLayout()
        news_layout.addWidget(self.news_text_box)  # Add text box for news content

        # Horizontal layout for aligning the link label to the right
        link_layout = QtWidgets.QHBoxLayout()
        link_layout.addStretch()  # Push the label to the right
        link_layout.addWidget(self.news_link_label)
        news_layout.addLayout(link_layout)  # Add the link layout to the main news layout

        # Main horizontal layout to place left and right sections side by side
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(news_layout)  # Add news content section

        # Create main widget to hold layout
        widget = QtWidgets.QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # Add annotation text (hidden by default)
        self.annotation = self.sc.axes.annotate(
            "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->")
        )
        self.annotation.set_visible(False)

        # Connect mouse motion event
        self.sc.mpl_connect("motion_notify_event", self.on_hover)

        # Connect click event for markers
        self.sc.mpl_connect("pick_event", self.on_pick)

        self.show()

    def fetch_symbols(self):
        # Connect to the database and retrieve unique symbols
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="finance_nifty50"
        )
        
        query = "SELECT DISTINCT Symbol FROM stockprices"
        symbols = []
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                symbols = [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
        
        return symbols

    def fetch_data_from_mysql(self, start_dt, end_dt, symbol):
        # Establish a connection to your MySQL database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="finance_nifty50"
        )

        # Modified query with the WHERE clause filtering for selected Symbol
        query = """
            SELECT Date, Close 
            FROM stockprices
            WHERE Date BETWEEN %s AND %s
            AND Symbol = %s
        """
        params = (start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'), symbol)
        
        # Fetch data into a DataFrame
        df = pd.read_sql(query, conn, params=params)
        conn.close()

        # Set the Date column as the index
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        return df

    def fetch_news_data(self, start_dt, end_dt, symbol):
        # Establish a connection to your MySQL database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="finance_nifty50"
        )

        # Query to fetch news data with news_date, news_polarity, news_content, and news_link
        query = """
            SELECT news_date, news_polarity, news_content, news_link
            FROM newscrawl
            WHERE news_date BETWEEN %s AND %s
            AND news_content LIKE %s
        """
        Symbolx = symbol.replace(".JK", "")
        params = (start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'), f"%{Symbolx}%")
        
        # Fetch data into a DataFrame
        news_df = pd.read_sql(query, conn, params=params)
        conn.close()

        # Convert news_date to datetime and set as index
        news_df['news_date'] = pd.to_datetime(news_df['news_date'])
        news_df.set_index('news_date', inplace=True)

        return news_df

    def update_plot(self):
        # Get the selected start and end dates and symbol
        start_dt = self.start_date.dateTime().toPyDateTime()
        end_dt = self.end_date.dateTime().toPyDateTime()

        # Get the current symbol and fetch data from MySQL
        symbol = self.symbol_selector.currentText()
        self.df = self.fetch_data_from_mysql(start_dt, end_dt, symbol)

        # Remove ".JK" suffix from symbol for fetching news data
        symbol = symbol.replace(".JK", "")
        self.news_df = self.fetch_news_data(start_dt, end_dt, symbol)  # Fetch news data with polarity and content

        # Clear the previous plot
        self.sc.axes.clear()

        # Check if self.df is empty
        if self.df.empty:
            print("No price data available for the selected date range and symbol.")
            self.sc.draw()
            return

        # Plot the main data (Close prices)
        self.line, = self.sc.axes.plot(self.df.index, self.df['Close'], color="blue", label="Close Price", picker=5)

        # Set the y-axis label and title
        self.sc.axes.set_title(f"{symbol} Close Price from {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
        self.sc.axes.set_xlabel("Date")
        self.sc.axes.set_ylabel("Close Price")

        # Check if self.news_df is empty
        if not self.news_df.empty:
            # Overlay news points based on polarity, along the Close line
            for news_date, row in self.news_df.iterrows():
                # Find the closest date in self.df to the news_date
                if news_date in self.df.index:
                    closest_date = news_date
                else:
                    # Find nearest date if exact date is not available
                    closest_date = self.df.index[np.argmin(np.abs(self.df.index - news_date))]

                # Get the Close price at the closest date
                y_value = self.df['Close'].loc[closest_date]

                # Set marker color based on polarity
                color = 'green' if row['news_polarity'] == 'Positive' else 'red'
                
                # Plot the news marker along the Close price line at the corresponding (or nearest) date
                marker = self.sc.axes.plot(closest_date, y_value, 'o', color=color, markersize=6, picker=5)
                
                # Attach news content to the marker for easy access
                marker[0].news_content = row['news_content']
                marker[0].news_link = row['news_link']
        # Add legend for the Close Price line only
        self.sc.axes.legend(loc="upper left")

        # Redraw the canvas
        self.sc.draw()

    def on_pick(self, event):
        # Check if the picked object has news_content and news_link
        if hasattr(event.artist, 'news_content') and hasattr(event.artist, 'news_link'):
            # Display the news content in the text box
            self.news_text_box.setText(event.artist.news_content)
            
            # Set hyperlink in label with target attribute for clarity
            link = event.artist.news_link
            self.news_link_label.setText(f'<a href="{link}" target="_blank">Read full article</a>')
            self.news_link_label.show()
        else:
            # Clear the text box and hyperlink label if no content is found
            self.news_text_box.clear()
            self.news_link_label.clear()
            
    def open_link(self, link):
        # Open the link in the default web browser
        webbrowser.open(link)         
    
    def on_hover(self, event):
        # Check if the mouse is over the plot area and self.df is not empty
        if event.inaxes == self.sc.axes and not self.df.empty:
            # Get the closest data point
            if event.xdata and event.ydata:
                # Convert event xdata to a datetime to match the index
                mouse_x_date = pd.to_datetime(event.xdata, unit='s', origin='unix')
                
                # Calculate the absolute difference and find the index of the closest point
                xdata = self.df.index
                closest_index = np.argmin(np.abs(xdata - mouse_x_date))
                closest_x = xdata[closest_index]
                closest_y = self.df['Close'].iloc[closest_index]

                # Set a threshold for proximity to show annotation
                dist = abs(mouse_x_date - closest_x).total_seconds()
                if dist < 86400:  # Show if within 1 day
                    # Update annotation text and position
                    self.annotation.xy = (closest_x, closest_y)
                    text = f"Date: {closest_x.strftime('%Y-%m-%d')}\nClose: {closest_y:.2f}"
                    self.annotation.set_text(text)
                    self.annotation.set_visible(True)
                    self.sc.draw_idle()
                else:
                    self.annotation.set_visible(False)
                    self.sc.draw_idle()
        else:
            # Hide the annotation if not hovering over a plot line
            self.annotation.set_visible(False)
            self.sc.draw_idle()



app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()