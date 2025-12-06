import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

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
    
    def get_city_coordinates(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude for a city"""
        try:
            # First, get the grid point for the city
            url = f"{self.base_url}/points/{city},{state}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return (data['properties']['relativeLocation']['geometry']['coordinates'][1],
                        data['properties']['relativeLocation']['geometry']['coordinates'][0])
            else:
                # Try alternative approach
                url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&country=US"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        return (data['results'][0]['latitude'], data['results'][0]['longitude'])
                
                logger.error(f"Failed to get coordinates for {city}, {state}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting coordinates for {city}, {state}: {str(e)}")
            return None
    
    def get_weather_data(self, city: str, state: str) -> Optional[Dict]:
        """Get current weather data for a city"""
        try:
            coordinates = self.get_city_coordinates(city, state)
            if not coordinates:
                return None
            
            lat, lon = coordinates
            
            # Get the grid point for these coordinates
            url = f"{self.base_url}/points/{lat},{lon}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get grid point for {city}, {state}: {response.status_code}")
                return None
            
            data = response.json()
            grid_id = data['properties']['gridId']
            grid_x = data['properties']['gridX']
            grid_y = data['properties']['gridY']
            
            # Get the forecast
            url = f"{self.base_url}/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get forecast for {city}, {state}: {response.status_code}")
                return None
            
            forecast_data = response.json()
            
            # Get the hourly forecast
            url = f"{self.base_url}/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast/hourly"
            response = requests.get(url, headers=self.headers)
            
            hourly_data = None
            if response.status_code == 200:
                hourly_data = response.json()
            
            # Get the observation stations
            url = f"{self.base_url}/gridpoints/{grid_id}/{grid_x},{grid_y}/stations"
            response = requests.get(url, headers=self.headers)
            
            stations_data = None
            if response.status_code == 200:
                stations_data = response.json()
            
            # Get alerts
            url = f"{self.base_url}/alerts/active?area={state}"
            response = requests.get(url, headers=self.headers)
            
            alerts_data = None
            if response.status_code == 200:
                alerts_data = response.json()
            
            # Get radar images
            radar_images = self.get_radar_images(lat, lon)
            
            return {
                'city': city,
                'state': state,
                'coordinates': coordinates,
                'forecast': forecast_data,
                'hourly': hourly_data,
                'stations': stations_data,
                'alerts': alerts_data,
                'radar_images': radar_images,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting weather data for {city}, {state}: {str(e)}")
            return None
    
    def get_radar_images(self, lat: float, lon: float) -> List[Dict]:
        """Get radar images for the specified coordinates"""
        try:
            # Get the nearest radar station
            url = f"https://api.weather.gov/radar/stations"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get radar stations: {response.status_code}")
                return []
            
            data = response.json()
            stations = data.get('features', [])
            
            # Find the nearest station (simplified - in production, calculate actual distance)
            nearest_station = None
            if stations:
                nearest_station = stations[0]['properties']['stationId']
            
            if not nearest_station:
                return []
            
            # Get radar images for the station
            images = []
            
            # Get the latest radar image
            url = f"https://api.weather.gov/radar/stations/{nearest_station}/images"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                for img in data.get('@graph', []):
                    if img.get('@type') == 'RadarImage':
                        images.append({
                            'url': img.get('url'),
                            'title': img.get('title'),
                            'description': img.get('description'),
                            'date': img.get('date')
                        })
            
            return images
        except Exception as e:
            logger.error(f"Error getting radar images: {str(e)}")
            return []
    
    def get_zone_weather_data(self, zone_name: str) -> List[Dict]:
        """Get weather data for all cities in a zone"""
        from zones import get_all_cities_in_zone
        
        cities = get_all_cities_in_zone(zone_name)
        weather_data = []
        
        for city in cities:
            # Extract state from city name (assuming format "City, State")
            if ", " in city:
                city_name, state = city.split(", ", 1)
                data = self.get_weather_data(city_name, state)
                if data:
                    weather_data.append(data)
        
        return weather_data