import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(message)s'
)

def main():
    """Main entry point of the application."""
    logging.info("Logging is configured and main.py is running.")

if __name__ == "__main__":
    main() 