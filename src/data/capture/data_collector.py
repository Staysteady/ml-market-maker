import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DataCollector:
    """Collects and prepares data for model training."""
    
    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """Initialize data collector.
        
        Args:
            db_manager: Database manager for retrieving data
            config: Configuration dictionary
        """
        self.db_manager = db_manager
        self.config = config
        
    def get_training_data(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[float]]]:
        """Get training data and user adjustments.
        
        Args:
            start_time: Optional start time for data collection
            end_time: Optional end time for data collection
            
        Returns:
            Tuple of (market states list, user adjustments dictionary)
        """
        try:
            # Get market snapshots
            snapshots = self._get_market_snapshots(start_time, end_time)
            
            # Get user adjustments
            adjustments = self._get_user_adjustments(start_time, end_time)
            
            # Process into training format
            market_states = self._process_snapshots(snapshots)
            user_adj_dict = self._process_adjustments(adjustments)
            
            return market_states, user_adj_dict
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            raise
            
    def _get_market_snapshots(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> pd.DataFrame:
        """Get market snapshots from database.
        
        Args:
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            DataFrame of market snapshots
        """
        query = """
        SELECT * FROM market_snapshots
        WHERE 1=1
        """
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
            
        query += " ORDER BY timestamp ASC"
        
        return pd.read_sql_query(
            query,
            self.db_manager._get_connection(),
            params=params,
            parse_dates=['timestamp']
        )
        
    def _get_user_adjustments(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> pd.DataFrame:
        """Get user adjustments from database.
        
        Args:
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            DataFrame of user adjustments
        """
        query = """
        SELECT * FROM user_adjustments
        WHERE 1=1
        """
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
            
        query += " ORDER BY timestamp ASC"
        
        return pd.read_sql_query(
            query,
            self.db_manager._get_connection(),
            params=params,
            parse_dates=['timestamp']
        )
        
    def _process_snapshots(
        self,
        snapshots: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Process snapshots into training format.
        
        Args:
            snapshots: DataFrame of market snapshots
            
        Returns:
            List of market state dictionaries
        """
        # Group by timestamp
        grouped = snapshots.groupby('timestamp')
        
        market_states = []
        for timestamp, group in grouped:
            state = {}
            
            # Group by instrument
            for instrument, inst_data in group.groupby('instrument_id'):
                state[instrument] = {
                    'bid': pd.Series(inst_data['bid_price'].values),
                    'ask': pd.Series(inst_data['ask_price'].values)
                }
                
            market_states.append(state)
            
        return market_states
        
    def _process_adjustments(
        self,
        adjustments: pd.DataFrame
    ) -> Dict[str, List[float]]:
        """Process user adjustments into training format.
        
        Args:
            adjustments: DataFrame of user adjustments
            
        Returns:
            Dictionary of adjustment lists by instrument
        """
        adj_dict = {}
        
        for _, row in adjustments.iterrows():
            instrument = row['instrument_id']
            if instrument not in adj_dict:
                adj_dict[instrument] = []
            
            # Calculate adjustment amount
            adjustment = row['new_mid'] - row['old_mid']
            adj_dict[instrument].append(adjustment)
            
        return adj_dict 