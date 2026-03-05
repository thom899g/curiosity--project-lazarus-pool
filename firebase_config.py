"""
Firebase configuration and initialization module.
Handles Firestore connection with proper error handling and reconnection logic.
"""

import os
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseManager:
    """Manages Firebase connection with singleton pattern and error recovery."""
    
    _instance = None
    _db = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance
    
    def initialize(self, service_account_key_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase connection with error handling.
        
        Args:
            service_account_key_path: Path to Firebase service account key JSON
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            logger.info("Firebase already initialized")
            return True
        
        try:
            # Get key path from environment if not provided
            if not service_account_key_path:
                service_account_key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')
            
            if not service_account_key_path:
                logger.error("Firebase service account key path not provided")
                return False
            
            # Verify file exists
            key_path = Path(service_account_key_path)
            if not key_path.exists():
                logger.error(f"Firebase key file not found: {service_account_key_path}")
                return False
            
            # Initialize Firebase app
            cred = credentials.Certificate(str(key_path))
            
            # Check if app already exists
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            # Initialize Firestore
            self._db = firestore.client()
            self._initialized = True
            
            logger.info("Firebase initialized successfully")
            
            # Test connection
            test_doc = self._db.collection('system_health').document('connection_test')
            test_doc.set({'test': True, 'timestamp': firestore.SERVER_TIMESTAMP})
            test_doc.delete()
            
            logger.debug("Firebase connection test passed")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"