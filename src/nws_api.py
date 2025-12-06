# src/nws_api.py

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time

from config import Config

logger = logging.getLogger(__name__)

class NWSAPI:
    def __init__(self):
        self.api_key = Config.NWS_API_KEY
        self.user_agent = Config.NWS_USER_AGENT
        self.base_url = "https://api.weather.gov"
        self.headers = {
            'User-Agent': self.user_agent,
            'API-Key': self.api_key,
            'Accept': 'application/json'
        }
        self.timeout = 10  # Timeout in seconds for API requests
    
    def get_city_coordinates(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude for a city"""
        try:
            # First, try to get grid point for city
            url = f"{self.base_url}/points/{city},{state}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return (data['properties']['relativeLocation']['geometry']['coordinates'][1],
                        data['properties']['relativeLocation']['geometry']['coordinates'][0])
            else:
                # Try alternative approach using Open-Meteo API
                url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&country=US"
                response = requests.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        return (data['results'][0]['latitude'], data['results'][0]['longitude'])
                
                logger.error(f"Failed to get coordinates for {city}, {state}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting coordinates for {city}, {state}: {str(e)}")
            return None
    
    def get_weather_data(self, city: str, state: str, grid_id: str, grid_x: int, grid_y: int) -> Optional[Dict]:
        """Get current weather data for a city using pre-defined grid information"""
        try:
            # Get forecast using provided grid information
            url = f"{self.base_url}/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code != 200:
                logger.error(f"Failed to get forecast for {city}, {state}: {response.status_code}")
                return None
            
            forecast_data = response.json()
            
            # Get hourly forecast
            url = f"{self.base_url}/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast/hourly"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            hourly_data = None
            if response.status_code == 200:
                hourly_data = response.json()
            
            # Get alerts
            url = f"{self.base_url}/alerts/active?area={state}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            alerts_data = None
            if response.status_code == 200:
                alerts_data = response.json()
            
            # Get radar images (simplified to avoid 'stationId' error)
            radar_images = []
            
            return {
                'city': city,
                'state': state,
                'grid_id': grid_id,
                'grid_x': grid_x,
                'grid_y': grid_y,
                'forecast': forecast_data,
                'hourly': hourly_data,
                'alerts': alerts_data,
                'radar_images': radar_images,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting weather data for {city}, {state}: {str(e)}")
            return None
    
    def get_zone_weather_data(self, zone_name: str) -> List[Dict]:
    """Get weather data for all cities in a zone"""
    from zones import get_all_city_info_in_zone
    
    cities_info = get_all_city_info_in_zone(zone_name)
    weather_data = []
    
    for city_info in cities_info:
        city = city_info['city']
        state = city.split(', ')[1] if ', ' in city else ''
        grid_id = city_info['grid_id']
        grid_x = city_info['grid_x']
        grid_y = city_info['grid_y']
        
        # Get weather data for this city
        try:
            data = self.get_weather_data(city, state, grid_id, grid_x, grid_y)
            if data:
                weather_data.append(data)
        except Exception as e:
            logger.error(f"Error getting weather data for {city}: {str(e)}")
            # Continue with other cities even if one fails
        
        # Add a small delay to avoid hitting rate limits
        time.sleep(0.5)
    
    return weather_data