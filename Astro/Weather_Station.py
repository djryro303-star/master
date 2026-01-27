#!/usr/bin/env python3
"""
Ecowitt Weather Station to Wunderground Uploader
Pulls data from local Ecowitt weather station and cloud coverage from OpenWeatherMap,
then uploads combined data to Wunderground.
"""

import requests
import json
import time
import logging
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Container for combined weather data"""
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: int
    rainfall: float
    cloud_coverage: int
    timestamp: datetime


class EcowittWeatherStation:
    """Retrieve data from local Ecowitt weather station"""
    
    def __init__(self, gateway_ip: str, gateway_port: int = 8000):
        """
        Initialize Ecowitt gateway connection
        
        Args:
            gateway_ip: IP address of Ecowitt gateway (e.g., "192.168.1.100")
            gateway_port: Port number (default 8000)
        """
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.base_url = f"http://{gateway_ip}:{gateway_port}"
        self.timeout = 10
        
    def get_local_data(self) -> Optional[Dict]:
        """
        Fetch weather data from local Ecowitt gateway
        
        Returns:
            Dictionary of weather data or None if request fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/get_stations",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully retrieved data from Ecowitt gateway")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve data from Ecowitt: {e}")
            return None
    
    def parse_data(self, raw_data: Dict) -> Optional[Dict]:
        """
        Parse Ecowitt raw data into usable format
        
        Args:
            raw_data: Raw response from Ecowitt gateway
            
        Returns:
            Parsed weather data dictionary
        """
        try:
            # Adjust these mappings based on your station's output
            # Common Ecowitt fields:
            parsed = {
                'temperature': raw_data.get('outdoor', {}).get('temperature'),
                'humidity': raw_data.get('outdoor', {}).get('humidity'),
                'pressure': raw_data.get('pressure'),
                'wind_speed': raw_data.get('wind', {}).get('windspeed'),
                'wind_direction': raw_data.get('wind', {}).get('winddir'),
                'rainfall': raw_data.get('rain', {}).get('rainevent'),
            }
            logger.debug(f"Parsed Ecowitt data: {parsed}")
            return parsed
        except Exception as e:
            logger.error(f"Error parsing Ecowitt data: {e}")
            return None


class CloudCoverageProvider:
    """Retrieve cloud coverage data from OpenWeatherMap"""
    
    def __init__(self, api_key: str, latitude: float, longitude: float):
        """
        Initialize OpenWeatherMap API client
        
        Args:
            api_key: OpenWeatherMap API key (free tier available)
            latitude: Station latitude
            longitude: Station longitude
        """
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.timeout = 10
        
    def get_cloud_coverage(self) -> Optional[int]:
        """
        Fetch cloud coverage percentage
        
        Returns:
            Cloud coverage as percentage (0-100) or None if request fails
        """
        try:
            params = {
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.api_key
            }
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            cloud_coverage = data.get('clouds', {}).get('all', 0)
            logger.info(f"Cloud coverage: {cloud_coverage}%")
            return cloud_coverage
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve cloud data: {e}")
            return None


class WundergroundUploader:
    """Upload weather data to Wunderground"""
    
    def __init__(self, station_id: str, station_key: str):
        """
        Initialize Wunderground uploader
        
        Args:
            station_id: Your Wunderground station ID
            station_key: Your Wunderground station API key
        """
        self.station_id = station_id
        self.station_key = station_key
        self.upload_url = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
        self.timeout = 10
        
    def upload_data(self, weather_data: WeatherData) -> bool:
        """
        Upload combined weather data to Wunderground
        
        Args:
            weather_data: WeatherData object with all measurements
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Format data for Wunderground API
            params = {
                'ID': self.station_id,
                'PASSWORD': self.station_key,
                'dateutc': weather_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'tempf': weather_data.temperature,
                'humidity': weather_data.humidity,
                'baromin': weather_data.pressure,
                'windspeedmph': weather_data.wind_speed,
                'winddir': weather_data.wind_direction,
                'rainin': weather_data.rainfall,
                'clouds': weather_data.cloud_coverage,
                'action': 'updateraw',
                'realtime': 1,
                'rtfreq': 2880  # Update frequency in seconds
            }
            
            response = requests.get(
                self.upload_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if 'success' in response.text.lower():
                logger.info("Successfully uploaded data to Wunderground")
                return True
            else:
                logger.warning(f"Wunderground response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload to Wunderground: {e}")
            return False


class WeatherStationManager:
    """Orchestrate data collection and upload"""
    
    def __init__(
        self,
        ecowitt_ip: str,
        owm_api_key: str,
        station_latitude: float,
        station_longitude: float,
        wunderground_station_id: str,
        wunderground_api_key: str
    ):
        """
        Initialize the weather station manager
        
        Args:
            ecowitt_ip: IP address of Ecowitt gateway
            owm_api_key: OpenWeatherMap API key
            station_latitude: Station latitude for cloud data
            station_longitude: Station longitude for cloud data
            wunderground_station_id: Wunderground station ID
            wunderground_api_key: Wunderground API key
        """
        self.ecowitt = EcowittWeatherStation(ecowitt_ip)
        self.cloud_provider = CloudCoverageProvider(
            owm_api_key,
            station_latitude,
            station_longitude
        )
        self.uploader = WundergroundUploader(
            wunderground_station_id,
            wunderground_api_key
        )
        
    def collect_and_upload(self) -> bool:
        """
        Collect data from all sources and upload to Wunderground
        
        Returns:
            True if upload successful, False otherwise
        """
        # Get Ecowitt data
        raw_data = self.ecowitt.get_local_data()
        if not raw_data:
            logger.error("Failed to get Ecowitt data")
            return False
            
        ecowitt_data = self.ecowitt.parse_data(raw_data)
        if not ecowitt_data:
            logger.error("Failed to parse Ecowitt data")
            return False
        
        # Get cloud coverage
        cloud_coverage = self.cloud_provider.get_cloud_coverage()
        if cloud_coverage is None:
            logger.warning("Could not get cloud coverage, using 0")
            cloud_coverage = 0
        
        # Combine into WeatherData object
        weather_data = WeatherData(
            temperature=ecowitt_data.get('temperature', 0),
            humidity=ecowitt_data.get('humidity', 0),
            pressure=ecowitt_data.get('pressure', 0),
            wind_speed=ecowitt_data.get('wind_speed', 0),
            wind_direction=ecowitt_data.get('wind_direction', 0),
            rainfall=ecowitt_data.get('rainfall', 0),
            cloud_coverage=cloud_coverage,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Combined weather data: {weather_data}")
        
        # Upload to Wunderground
        return self.uploader.upload_data(weather_data)


def main():
    """Main entry point - configure with your settings"""
    
    # ============ CONFIGURATION ============
    # Ecowitt Gateway (local network)
    ECOWITT_GATEWAY_IP = "192.168.68.99"  # Change to your gateway IP
    
    # OpenWeatherMap (free API key from https://openweathermap.org/api)
    OWM_API_KEY = "613dfb5ea6b09dbb3044099e7d7fcf14"  # Get from openweathermap.org
    STATION_LATITUDE = 39.475052635243614 # Your station's latitude
    STATION_LONGITUDE = -105.06619364251313  # Your station's longitude
    
    # Wunderground
    WU_STATION_ID = "KCOLITTL1240"  # From Wunderground account
    WU_API_KEY = "your_stPavYJkc7ation_api_key"  # From Wunderground account
    
    # Update interval in seconds
    UPDATE_INTERVAL = 300  # 5 minutes
    # ======================================
    
    # Validate configuration
    if "your_" in OWM_API_KEY or "your_" in WU_STATION_ID:
        logger.error("Please configure API keys and station IDs in the script")
        return
    
    manager = WeatherStationManager(
        ecowitt_ip=ECOWITT_GATEWAY_IP,
        owm_api_key=OWM_API_KEY,
        station_latitude=STATION_LATITUDE,
        station_longitude=STATION_LONGITUDE,
        wunderground_station_id=WU_STATION_ID,
        wunderground_api_key=WU_API_KEY
    )
    
    logger.info("Starting Weather Station uploader")
    
    try:
        while True:
            logger.info("Collecting and uploading weather data...")
            manager.collect_and_upload()
            logger.info(f"Waiting {UPDATE_INTERVAL} seconds until next update")
            time.sleep(UPDATE_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Shutting down Weather Station uploader")


if __name__ == "__main__":
    main()
