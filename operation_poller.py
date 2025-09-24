#!/usr/bin/env python3
"""
Centralized operation polling logic.
"""

import time
import logging
from typing import List, Dict, Any, Optional

from user_creator import UserCreator
from exceptions import OperationError

logger = logging.getLogger(__name__)


class OperationPoller:
    """Handles polling of Yandex Cloud operations."""
    
    def __init__(self, user_creator: UserCreator):
        self.user_creator = user_creator
    
    def poll_pending_operations(self, pending_ops: List[Dict[str, Any]], 
                              operation_type: str = "operation") -> int:
        """Poll pending operations once and return count of successes."""
        successes = 0
        still_pending = []
        
        for item in pending_ops:
            op_id = item['operation_id']
            operation_name = item.get('folder_name', item.get('database_name', 'unknown'))
            
            try:
                data = self.user_creator.get_operation_status(op_id)
                done = data.get('done', False)
                
                if not done:
                    if self._has_operation_error(data):
                        self._log_operation_error(op_id, operation_name, data, operation_type)
                    else:
                        still_pending.append(item)
                    continue
                
                # Operation is done
                if self._has_operation_error(data):
                    self._log_operation_error(op_id, operation_name, data, operation_type, is_final=True)
                else:
                    self._log_operation_success(op_id, operation_name, item.get('start_time'))
                    successes += 1
                    
            except OperationError as e:
                logger.error(f"Polling error for {operation_type} {op_id} ({operation_name}): {e}")
                # Drop this operation to avoid infinite loop
        
        # Gentle pacing between poll cycles
        if still_pending:
            time.sleep(2)
        pending_ops[:] = still_pending
        return successes
    
    def _has_operation_error(self, data: Dict[str, Any]) -> bool:
        """Check if operation has an error."""
        return 'error' in data and data['error']
    
    def _log_operation_error(self, op_id: str, operation_name: str, 
                           data: Dict[str, Any], operation_type: str, 
                           is_final: bool = False) -> None:
        """Log operation error consistently."""
        err = data['error']
        status = err.get('code', 'unknown')
        message = err.get('message', 'no message')
        details = err.get('details', {})
        
        action = "failed" if is_final else "has failures"
        logger.error(
            f"YDB {operation_type} {op_id} for {operation_type} {operation_name} {action}: "
            f"status={status}, message={message}, details={details}"
        )
    
    def _log_operation_success(self, op_id: str, operation_name: str, 
                             start_time: Optional[float]) -> None:
        """Log operation success consistently."""
        elapsed_info = ""
        if start_time:
            try:
                elapsed = time.time() - start_time
                elapsed_info = f" in {elapsed:.1f}s"
            except Exception:
                pass
        
        logger.info(f"YDB operation {op_id} for {operation_name} completed successfully{elapsed_info}")
