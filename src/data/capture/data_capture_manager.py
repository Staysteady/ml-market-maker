import logging
from typing import Dict, Any, Optional, Deque
from collections import deque
import time
import threading
from datetime import datetime, time as dt_time

from ..excel.excel_reader import ExcelReader
from ..storage.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCaptureManager:
    """Manages the data capture process and stability checks."""
    
    def __init__(self, excel_reader: ExcelReader, config: Dict[str, Any], db_manager: DatabaseManager):
        """Initialize the data capture manager.
        
        Args:
            excel_reader: Configured ExcelReader instance
            config: Configuration dictionary
            db_manager: Database manager instance for storing data
        """
        self.reader = excel_reader
        self.config = config
        self.db_manager = db_manager
        self.stability_buffer: Deque = deque(maxlen=20)  # Store recent captures
        self.is_capturing: bool = False
        self.capture_thread: Optional[threading.Thread] = None
        
    def start_capture(self) -> None:
        """Begins the data capture process in a separate thread."""
        if self.is_capturing:
            logger.warning("Capture already running")
            return
            
        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        logger.info("Started data capture")
        
    def stop_capture(self) -> None:
        """Stops the data capture process."""
        self.is_capturing = False
        if self.capture_thread:
            self.capture_thread.join(timeout=10.0)
        logger.info("Stopped data capture")
        
    def _capture_loop(self) -> None:
        """Main capture loop."""
        while self.is_capturing:
            try:
                if not self._is_trading_hours():
                    time.sleep(60)  # Check every minute outside trading hours
                    continue
                    
                current_data = self.reader.read_market_data()
                
                if self._is_stable(current_data):
                    self._process_capture(current_data)
                    
                time.sleep(self.config['system']['capture_interval'])
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(self.config['system']['capture_interval'])
                
    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours."""
        now = datetime.now().time()
        start = dt_time.fromisoformat(self.config['system']['trading_hours']['start'])
        end = dt_time.fromisoformat(self.config['system']['trading_hours']['end'])
        return start <= now <= end
        
    def _is_stable(self, data: Dict[str, Any]) -> bool:
        """Checks if data meets stability criteria.
        
        Data is considered stable if:
        1. We have enough samples in the buffer
        2. Values haven't changed significantly in the stability window
        3. No missing or invalid values
        
        Args:
            data: Current market data snapshot
            
        Returns:
            bool: True if data is stable
        """
        try:
            self.stability_buffer.append(data)
            
            if len(self.stability_buffer) < 3:  # Need minimum samples
                return False
                
            # Check stability across recent samples
            window = list(self.stability_buffer)[-3:]  # Last 3 samples
            
            for section in data.keys():
                if not self._check_section_stability(section, window):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error checking stability: {e}")
            return False
            
    def _check_section_stability(self, section: str, window: list) -> bool:
        """Check if a specific section's data is stable."""
        if not window:
            return False
            
        # Get values for this section across the window
        try:
            if isinstance(window[0][section], dict):  # bid/ask section
                bids = [sample[section]['bid'] for sample in window]
                asks = [sample[section]['ask'] for sample in window]
                
                # Check if values are stable within tolerance
                return (self._values_stable(bids) and 
                        self._values_stable(asks))
            else:  # midpoint section
                values = [sample[section] for sample in window]
                return self._values_stable(values)
                
        except Exception as e:
            logger.error(f"Error checking section stability: {e}")
            return False
            
    def _values_stable(self, values: list) -> bool:
        """Check if a series of values is stable within tolerance."""
        if not values:
            return False
            
        # Convert to numpy arrays for easier comparison
        import numpy as np
        arr = np.array(values)
        
        # Check max deviation
        max_dev = np.max(np.abs(arr - arr.mean()))
        return max_dev <= self.config.get('stability_tolerance', 0.25)
        
    def _process_capture(self, data: Dict[str, Any]) -> None:
        """Process a stable data capture.
        
        Stores the captured data in the database and triggers any necessary
        analysis or visualization updates.
        
        Args:
            data: Market data dictionary
        """
        try:
            # Store the snapshot in the database
            self.db_manager.store_snapshot(data)
            logger.info("Processed and stored stable data capture")
            
        except Exception as e:
            logger.error(f"Error processing capture: {e}")
            # Continue capturing despite storage errors 