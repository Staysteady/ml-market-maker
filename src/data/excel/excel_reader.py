import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import pandas as pd
import numpy as np
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelReader:
    def __init__(self, config_path: str):
        """Initialize Excel reader with configuration.
        
        Args:
            config_path: Path to the configuration YAML file
        """
        self.config = self._load_config(config_path)
        self.file_path: Optional[Path] = None
        self.last_modified: Optional[float] = None
        self.watch_callback: Optional[Callable] = None
        self.watching: bool = False
        
    def set_watch_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback function to be called when file changes are detected.
        
        Args:
            callback: Function that takes market data dictionary as argument
        """
        self.watch_callback = callback
        
    def start_watching(self, interval: float = 5.0) -> None:
        """Start watching file for changes.
        
        Args:
            interval: Time between checks in seconds
        """
        if not self.file_path:
            raise ValueError("File path not set. Call set_file_path() first.")
            
        if not self.watch_callback:
            raise ValueError("Watch callback not set. Call set_watch_callback() first.")
            
        self.watching = True
        logger.info(f"Started watching {self.file_path}")
        
        while self.watching:
            try:
                current_mtime = os.path.getmtime(self.file_path)
                
                if self.last_modified is None or current_mtime > self.last_modified:
                    logger.debug(f"File change detected at {current_mtime}")
                    data = self.read_market_data()
                    
                    if self.validate_data(data):
                        self.last_modified = current_mtime
                        self.watch_callback(data)
                        
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error while watching file: {e}")
                # Continue watching despite errors
                time.sleep(interval)
                
    def stop_watching(self) -> None:
        """Stop watching file for changes."""
        self.watching = False
        logger.info("Stopped watching file")

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validates captured data meets requirements.
        
        Checks:
        1. All required sections are present
        2. Data is within expected ranges
        3. Bid/ask spreads are valid
        4. No missing or invalid values
        
        Args:
            data: Dictionary containing market data sections
            
        Returns:
            bool: True if data is valid, False otherwise
            
        Raises:
            ValueError: If validation fails with specific reason
        """
        try:
            # Check all required sections exist
            required_sections = {'section1', 'section2', 'section3'}
            if not all(section in data for section in required_sections):
                missing = required_sections - set(data.keys())
                raise ValueError(f"Missing required sections: {missing}")
                
            # Validate each section's data
            for section_name, section_data in data.items():
                if isinstance(section_data, dict):  # bid/ask sections
                    self._validate_bid_ask_section(section_name, section_data)
                else:  # midpoint sections
                    self._validate_midpoint_section(section_name, section_data)
                    
            return True
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            raise
            
    def _validate_bid_ask_section(self, section_name: str, section_data: Dict[str, pd.Series]):
        """Validates bid/ask data section."""
        if not {'bid', 'ask'}.issubset(section_data.keys()):
            raise ValueError(f"Missing bid or ask data in {section_name}")
            
        bid, ask = section_data['bid'], section_data['ask']
        
        # Check for missing values
        if bid.isna().any() or ask.isna().any():
            raise ValueError(f"Missing values in {section_name}")
            
        # Validate bid-ask relationship
        if not (ask >= bid).all():
            raise ValueError(f"Invalid bid-ask relationship in {section_name}")
            
        # Validate price increments based on instrument
        self._validate_price_increments(section_name, bid, ask)
            
    def _validate_midpoint_section(self, section_name: str, data: pd.Series):
        """Validates midpoint data section."""
        if data.isna().any():
            raise ValueError(f"Missing values in {section_name} midpoints")
            
    def _validate_price_increments(self, section_name: str, bid: pd.Series, ask: pd.Series):
        """Validates price increments meet requirements."""
        # Price increments: 0.25 for AH,CA,PB,ZS; 0.5 for NI and TIN
        increment = 0.5 if section_name in ['NI', 'TIN'] else 0.25
        
        # Check bid increments
        bid_mod = bid % increment
        if not np.allclose(bid_mod, 0, atol=1e-10) and not np.allclose(bid_mod, increment, atol=1e-10):
            raise ValueError(f"Invalid bid price increments in {section_name}")
            
        # Check ask increments
        ask_mod = ask % increment
        if not np.allclose(ask_mod, 0, atol=1e-10) and not np.allclose(ask_mod, increment, atol=1e-10):
            raise ValueError(f"Invalid ask price increments in {section_name}") 