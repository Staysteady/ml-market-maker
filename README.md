# Sales Data Analysis Project

A simple Python project that loads sales data from a CSV file and performs basic statistical calculations including total and average sales.

## Features
- Data loading from CSV
- Total sales calculation
- Average sales calculation
- Comprehensive logging
- Error handling for file operations and data parsing

## Requirements
- Python 3.x
- CSV file with columns: Day, Sales

## Usage
1. Prepare your data in a CSV file named `data.csv` with the following format:
```csv
Day,Sales
1,100
2,150
3,200
```

2. Run the project:
```bash
python3 main.py
```

3. The program will output:
- Number of records loaded
- Total sales amount
- Average sales per day
- Detailed debug information (if needed)

## Example Output
```
INFO:Logging is configured and main.py is running.
INFO:Loaded 3 records from data.csv
INFO:Data loading completed successfully.
INFO:Total sales calculated: 450
INFO:Total sales: 450
INFO:Average sales calculated: 150.0
INFO:Average sales: 150.0
``` 