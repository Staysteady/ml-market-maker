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

def main():
    """Main entry point of the application."""
    logging.info("Logging is configured and main.py is running.")
    
    # Load the sales data
    data = load_data("data.csv")
    logging.info("Data loading completed successfully.")
    logging.debug(f"Loaded data: {data}")

if __name__ == "__main__":
    main() 