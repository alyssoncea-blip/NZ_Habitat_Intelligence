"""
API Client Module
Handles HTTP requests to data APIs with retry logic and pagination
"""
import time
import logging
import requests
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class APIClient:
    """Client for making API requests with retry logic"""
    
    def __init__(self, base_url: str, max_retries: int = 3, retry_delay: int = 1):
        """Initialize API client
        
        Args:
            base_url: Base URL for API
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
    
    def _get_with_retry(
        self,
        url: str,
        params: Optional[Dict] = None,
        max_retries: Optional[int] = None,
        backoff_factor: float = 0.5
    ) -> Dict[str, Any]:
        """Make GET request with retry logic
        
        Args:
            url: API endpoint URL
            params: Query parameters
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential retry
        
        Returns:
            JSON response as dictionary
        
        Raises:
            requests.RequestException: If all retries fail
        """
        last_exception = None
        max_retries = max_retries or self.max_retries
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"Request failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
        
        logger.error(f"All {max_retries} attempts failed for {url}")
        raise last_exception
    
    def fetch_data(
        self,
        endpoint: str,
        batch_size: Optional[int] = None,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """Fetch paginated data from API
        
        Args:
            endpoint: API endpoint path
            batch_size: Number of items per page (None uses API default)
            max_retries: Maximum retry attempts
        
        Returns:
            List of all records from all pages
        """
        all_data = []
        page = 1
        batch_size = batch_size or self.max_retries
        full_url = f"{self.base_url}{endpoint}"
        
        while True:
            params = {'page': page, 'limit': batch_size}
            
            try:
                data = self._get_with_retry(full_url, params, max_retries)
                
                # Handle different response formats
                if isinstance(data, dict):
                    if 'data' in data:
                        records = data['data']
                        has_more = data.get('has_more', False)
                    elif 'results' in data:
                        records = data['results']
                        has_more = data.get('pagination', {}).get('has_more', False)
                    else:
                        records = data
                        has_more = False
                else:
                    records = data
                    has_more = False
                
                if not records:
                    break
                
                all_data.extend(records)
                
                # Check if there are more pages
                if not has_more:
                    break
                
                page += 1
                
            except requests.RequestException as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                raise
        
        logger.info(f"Fetched {len(all_data)} records from {full_url}")
        return all_data

def create_api_client(config):
    """Create and return API client instance
    
    Args:
        config: Configuration object
    
    Returns:
        APIClient instance
    """
    base_url = config.get('API_BASE_URL', 'https://api.example.com')
    max_retries = int(config.get('MAX_RETRIES', 3))
    retry_delay = int(config.get('RETRY_DELAY', 1))
    return APIClient(base_url, max_retries, retry_delay)