import yfinance as yf
import mysql.connector

# Establish the database connection
db = mysql.connector.connect(
    host="localhost",          # Replace with your MySQL host
    user="root",           # Replace with your MySQL username
    password="-",   # Replace with your MySQL password
    database="finance_nifty50"    # Replace with your database name
)

# Create a cursor object
cursor = db.cursor()
# Execute a SQL query
query = "SELECT Symbol,Name FROM companies"  # Replace with your table name
cursor.execute(query)

# Fetch all rows from the executed query
rows = cursor.fetchall()
# Get column names
column_names = cursor.column_names

for rowx in rows:
    Symbol = rowx[0]      # Assuming 'id' is the first column
    Namex = rowx[1]    # Assuming 'name' is the second column
    #print(f"ID: {id_field}, Name: {name_field}")
    
    data = yf.download(Symbol, period="5y")
    for index, row in data.iterrows():
        #insert_query = f"""INSERT INTO StockPrices (Date, Open, High, Low, Close, Adj_Close, Volume, Symbol) 
        #                   VALUES ('{index.strftime('%Y-%m-%d')}', {row['Open']}, {row['High']}, {row['Low']}, {row['Close']}, {row['Adj Close']}, {row['Volume']}, '{rowx[0]}');"""
        insert_query = """INSERT INTO StockPrices (Date, Open, High, Low, Close, Adj_Close, Volume, Symbol)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        values = ((index.strftime('%Y-%m-%d'), float(row['Open'][0]), float(row['High'][0]), float(row['Low'][0]), float(row['Close'][0]), float(row['Adj Close'][0]), float(row['Volume'][0]), Symbol))
        cursor.execute(insert_query, values)
    print(Symbol)    
    db.commit()
# Committing the transaction and closing the connection

cursor.close()
db.close()

