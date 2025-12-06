import requests
import base64
import logging
from typing import Optional, Dict, List
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        pass
    
    def convert_to_base64(self, image_url: str) -> Optional[str]:
        """Convert an image from a URL to base64"""
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                image_bytes = response.content
                base64_bytes = base64.b64encode(image_bytes)
                base64_string = base64_bytes.decode('utf-8')
                return base64_string
            else:
                logger.error(f"Failed to fetch image: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            return None
    
    def generate_weather_card(self, city: str, state: str, temperature: int, condition: str, 
                             high_temp: int, low_temp: int, precipitation_chance: int) -> Optional[str]:
        """Generate a custom weather card image"""
        try:
            # Create a new image
            width, height = 800, 400
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Try to load a font (fallback to default if not available)
            try:
                title_font = ImageFont.truetype("arial.ttf", 36)
                temp_font = ImageFont.truetype("arial.ttf", 72)
                info_font = ImageFont.truetype("arial.ttf", 24)
            except:
                title_font = ImageFont.load_default()
                temp_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
            
            # Draw the city and state
            draw.text((50, 50), f"{city}, {state}", font=title_font, fill='black')
            
            # Draw the current temperature
            draw.text((50, 120), f"{temperature}°F", font=temp_font, fill='black')
            
            # Draw the condition
            draw.text((50, 220), condition, font=info_font, fill='black')
            
            # Draw high/low temperature
            draw.text((50, 280), f"H: {high_temp}°  L: {low_temp}°", font=info_font, fill='black')
            
            # Draw precipitation chance
            draw.text((50, 320), f"Precipitation: {precipitation_chance}%", font=info_font, fill='black')
            
            # Add a simple weather icon (simplified - in production, use actual weather icons)
            icon_x, icon_y = 500, 100
            icon_size = 150
            
            if "rain" in condition.lower() or "shower" in condition.lower():
                # Draw a simple rain cloud
                draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size/2], fill='gray')
                for i in range(5):
                    x = icon_x + 20 + i * 25
                    y = icon_y + icon_size/2
                    draw.line([x, y, x - 5, y + 20], fill='blue', width=3)
                    draw.line([x, y, x + 5, y + 20], fill='blue', width=3)
            elif "sun" in condition.lower() or "clear" in condition.lower():
                # Draw a simple sun
                draw.ellipse([icon_x + icon_size/4, icon_y + icon_size/4, 
                             icon_x + 3*icon_size/4, icon_y + 3*icon_size/4], fill='yellow')
                for angle in range(0, 360, 30):
                    import math
                    x1 = icon_x + icon_size/2 + (icon_size/2 - 10) * math.cos(math.radians(angle))
                    y1 = icon_y + icon_size/2 + (icon_size/2 - 10) * math.sin(math.radians(angle))
                    x2 = icon_x + icon_size/2 + icon_size/2 * math.cos(math.radians(angle))
                    y2 = icon_y + icon_size/2 + icon_size/2 * math.sin(math.radians(angle))
                    draw.line([x1, y1, x2, y2], fill='yellow', width=5)
            elif "cloud" in condition.lower():
                # Draw a simple cloud
                draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size/2], fill='lightgray')
                draw.ellipse([icon_x + icon_size/4, icon_y - icon_size/6, 
                             icon_x + 3*icon_size/4, icon_y + icon_size/3], fill='lightgray')
            else:
                # Draw a generic weather symbol
                draw.rectangle([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], fill='lightblue')
            
            # Add a timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            draw.text((50, 370), f"Updated: {timestamp}", font=info_font, fill='gray')
            
            # Convert the image to base64
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            image_bytes = buffer.getvalue()
            base64_bytes = base64.b64encode(image_bytes)
            base64_string = base64_bytes.decode('utf-8')
            
            return base64_string
        except Exception as e:
            logger.error(f"Error generating weather card: {str(e)}")
            return None
    
    def generate_weather_chart(self, hourly_data: List[Dict]) -> Optional[str]:
        """Generate a weather chart showing hourly temperature and precipitation"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            # Extract data for the chart
            hours = []
            temperatures = []
            precipitation = []
            
            for data in hourly_data[:24]:  # Limit to 24 hours
                if data.get('startTime') and data.get('temperature'):
                    # Extract hour from startTime
                    start_time = data['startTime']
                    hour = start_time.split('T')[1].split(':')[0] if 'T' in start_time else ''
                    hours.append(hour)
                    temperatures.append(data['temperature'])
                    
                    # Get precipitation probability if available
                    precip = 0
                    if data.get('probabilityOfPrecipitation') and data['probabilityOfPrecipitation'].get('value') is not None:
                        precip = data['probabilityOfPrecipitation']['value']
                    precipitation.append(precip)
            
            if not hours:
                logger.error("No valid hourly data for chart")
                return None
            
            # Create the chart
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            # Plot temperature
            color = 'tab:red'
            ax1.set_xlabel('Hour')
            ax1.set_ylabel('Temperature (°F)', color=color)
            ax1.plot(hours, temperatures, color=color, marker='o')
            ax1.tick_params(axis='y', labelcolor=color)
            
            # Create a second y-axis for precipitation
            ax2 = ax1.twinx()
            color = 'tab:blue'
            ax2.set_ylabel('Precipitation Chance (%)', color=color)
            ax2.bar(hours, precipitation, color=color, alpha=0.3)
            ax2.tick_params(axis='y', labelcolor=color)
            
            # Add title and layout adjustments
            plt.title('24-Hour Weather Forecast')
            fig.tight_layout()
            
            # Convert the chart to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            base64_bytes = base64.b64encode(image_bytes)
            base64_string = base64_bytes.decode('utf-8')
            
            return base64_string
        except Exception as e:
            logger.error(f"Error generating weather chart: {str(e)}")
            return None