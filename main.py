import logging
import csv
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(message)s'
)

def load_data(filepath: str) -> List[Tuple[int, int]]:
    """
    Load sales data from a CSV file.
    
    Args:
        filepath: Path to the CSV file containing sales data
        
    Returns:
        List of tuples containing (day, sales) records
    """
    records = []
    try:
        with open(filepath, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                day = int(row['Day'])
                sales = int(row['Sales'])
                records.append((day, sales))
        logging.info(f"Loaded {len(records)} records from {filepath}")
        return records
    except FileNotFoundError:
        logging.error(f"Data file not found: {filepath}")
        raise
    except (ValueError, KeyError) as e:
        logging.error(f"Error parsing data: {e}")
        raise

def calculate_total(data: List[Tuple[int, int]]) -> int:
    """
    Calculate the total sum of sales from the data.
    
    Args:
        data: List of (day, sales) tuples
        
    Returns:
        Total sales amount
    """
    total = sum(sales for _, sales in data)
    logging.info(f"Total sales calculated: {total}")
    return total

def calculate_average(data: List[Tuple[int, int]]) -> float:
    """
    Calculate the average sales from the data.
    
    Args:
        data: List of (day, sales) tuples
        
    Returns:
        Average sales amount
        
    Raises:
        ValueError: If data is empty
    """
    if not data:
        logging.error("Cannot calculate average: no data provided")
        raise ValueError("Cannot calculate average of empty dataset")
    
    total = calculate_total(data)
    average = total / len(data)
    logging.info(f"Average sales calculated: {average}")
    return average

def main():
    """Main entry point of the application."""
    logging.info("Logging is configured and main.py is running.")
    
    # Load the sales data
    data = load_data("data.csv")
    logging.info("Data loading completed successfully.")
    logging.debug(f"Loaded data: {data}")
    
    # Calculate total sales
    total_sales = calculate_total(data)
    logging.info(f"Total sales: {total_sales}")
    
    # Calculate average sales
    avg_sales = calculate_average(data)
    logging.info(f"Average sales: {avg_sales}")

if __name__ == "__main__":
    main() 