import json
import logging
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime
import re

from config import Config
from seo_optimizer import SEOOptimizer
from image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.seo_optimizer = SEOOptimizer()
        self.image_processor = ImageProcessor()
    
    def generate_blog_post(self, zone_name: str, weather_data: List[Dict]) -> Dict:
        """Generate a complete blog post for a zone"""
        try:
            # Generate the main content
            content = self._generate_content(zone_name, weather_data)
            
            # Generate SEO elements
            title = self._generate_title(zone_name, weather_data)
            meta_description = self._generate_meta_description(zone_name, weather_data)
            keywords = self._generate_keywords(zone_name, weather_data)
            
            # Generate schema markup
            schema_markup = self._generate_schema_markup(zone_name, weather_data)
            
            # Process images
            images = self._process_images(weather_data)
            
            # Generate related cities links
            related_links = self._generate_related_links(zone_name, weather_data)
            
            # Generate FAQs
            faqs = self._generate_faqs(weather_data)
            
            # Generate "What You Need to Know" section
            need_to_know = self._generate_need_to_know(weather_data)
            
            # Create the complete blog post
            blog_post = {
                'title': title,
                'meta_description': meta_description,
                'keywords': keywords,
                'content': content,
                'schema_markup': schema_markup,
                'images': images,
                'related_links': related_links,
                'faqs': faqs,
                'need_to_know': need_to_know,
                'zone_name': zone_name,
                'last_updated': datetime.now().isoformat(),
                'word_count': len(re.findall(r'\w+', content))
            }
            
            # Ensure minimum word count
            if blog_post['word_count'] < Config.MIN_WORD_COUNT:
                logger.warning(f"Generated content is below minimum word count: {blog_post['word_count']}")
                # In a production environment, you might want to regenerate or append additional content
            
            return blog_post
        except Exception as e:
            logger.error(f"Error generating blog post: {str(e)}")
            raise
    
    def _generate_content(self, zone_name: str, weather_data: List[Dict]) -> str:
        """Generate the main content of the blog post"""
        try:
            # Prepare the data for the prompt
            cities_data = []
            for data in weather_data:
                city_info = {
                    'city': data['city'],
                    'state': data['state'],
                    'coordinates': data['coordinates'],
                    'forecast': data['forecast']['properties']['periods'][:6] if data.get('forecast') and data['forecast'].get('properties') else [],
                    'hourly': data['hourly']['properties']['periods'][:12] if data.get('hourly') and data['hourly'].get('properties') else [],
                    'alerts': data['alerts']['features'][:3] if data.get('alerts') and data['alerts'].get('features') else []
                }
                cities_data.append(city_info)
            
            # Create the prompt for Gemini
            prompt = f"""
            Create a comprehensive, engaging, and SEO-optimized weather blog post for the {zone_name} Zone of the United States.
            
            The post should be at least 1000 words and include:
            
            1. An engaging introduction that captures the reader's attention and provides an overview of the weather patterns in the {zone_name} Zone.
            
            2. Detailed weather forecasts for each city, including:
               - Current conditions
               - Hourly forecast for the next 12 hours
               - Extended forecast for the next 6 days
               - Temperature trends
               - Precipitation chances
               - Wind conditions
               - Any weather alerts or warnings
            
            3. Analysis of weather patterns across the zone, highlighting similarities and differences between cities.
            
            4. Impact of weather on daily activities, travel, and outdoor plans.
            
            5. Historical context or interesting weather facts for the region.
            
            6. Safety tips and recommendations based on current weather conditions.
            
            7. A conclusion that summarizes the key weather information and provides a forward-looking perspective.
            
            The tone should be informative yet engaging, with a focus on practical information that helps readers plan their day.
            
            Do not mention that this content is AI-generated. Write as if you are a professional weather blogger.
            
            Here is the weather data for the cities in the {zone_name} Zone:
            
            {json.dumps(cities_data, indent=2)}
            
            Please format the content with appropriate headings, subheadings, and paragraphs to ensure readability and SEO optimization.
            """
            
            # Generate the content
            response = self.model.generate_content(prompt)
            content = response.text
            
            # Add the disclaimer
            disclaimer = """
            
            <div style="margin-top: 40px; padding: 15px; background-color: #f5f5f5; border-left: 4px solid #ccc;">
                <p><strong>Disclaimer:</strong> This post is created using the public data provided by the National Weather Service. Please check the <a href="https://www.weather.gov/" target="_blank">Original source</a> for more information.</p>
            </div>
            """
            
            return content + disclaimer
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            raise
    
    def _generate_title(self, zone_name: str, weather_data: List[Dict]) -> str:
        """Generate an SEO-optimized title for the blog post"""
        try:
            # Get the current date
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Get the main weather condition from the first city
            main_condition = "Variable Conditions"
            if weather_data and weather_data[0].get('forecast') and weather_data[0]['forecast'].get('properties'):
                periods = weather_data[0]['forecast']['properties']['periods']
                if periods:
                    main_condition = periods[0].get('shortForecast', 'Variable Conditions')
            
            # Create a prompt for title generation
            prompt = f"""
            Generate an SEO-optimized, click-worthy title for a weather blog post about the {zone_name} Zone of the United States.
            
            The title should:
            - Be under 60 characters
            - Include the zone name ({zone_name})
            - Include the current date ({current_date})
            - Include the main weather condition ({main_condition})
            - Be engaging and encourage clicks
            - Be optimized for Google Discover
            
            Do not mention that this content is AI-generated.
            
            Return only the title, without quotes or any additional text.
            """
            
            # Generate the title
            response = self.model.generate_content(prompt)
            title = response.text.strip()
            
            # Ensure the title is not too long
            if len(title) > 60:
                title = title[:57] + "..."
            
            return title
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            # Fallback title
            return f"{zone_name} Zone Weather Update: {current_date}"
    
    def _generate_meta_description(self, zone_name: str, weather_data: List[Dict]) -> str:
        """Generate an SEO-optimized meta description for the blog post"""
        try:
            # Get the current date
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Get a summary of the weather conditions
            conditions_summary = "variable weather conditions"
            if weather_data:
                conditions = []
                for data in weather_data[:3]:  # Just use the first 3 cities for brevity
                    if data.get('forecast') and data['forecast'].get('properties'):
                        periods = data['forecast']['properties']['periods']
                        if periods:
                            conditions.append(f"{data['city']}: {periods[0].get('shortForecast', 'Variable Conditions')}")
                
                if conditions:
                    conditions_summary = "; ".join(conditions)
            
            # Create a prompt for meta description generation
            prompt = f"""
            Generate an SEO-optimized meta description for a weather blog post about the {zone_name} Zone of the United States.
            
            The meta description should:
            - Be under 160 characters
            - Include the zone name ({zone_name})
            - Include the current date ({current_date})
            - Summarize the key weather conditions: {conditions_summary}
            - Be engaging and encourage clicks
            - Include a call to action
            
            Do not mention that this content is AI-generated.
            
            Return only the meta description, without quotes or any additional text.
            """
            
            # Generate the meta description
            response = self.model.generate_content(prompt)
            meta_description = response.text.strip()
            
            # Ensure the meta description is not too long
            if len(meta_description) > 160:
                meta_description = meta_description[:157] + "..."
            
            return meta_description
        except Exception as e:
            logger.error(f"Error generating meta description: {str(e)}")
            # Fallback meta description
            return f"Get the latest weather update for the {zone_name} Zone on {current_date}. Detailed forecasts for all major cities."
    
    def _generate_keywords(self, zone_name: str, weather_data: List[Dict]) -> List[str]:
        """Generate SEO keywords for the blog post"""
        try:
            keywords = [f"{zone_name} Zone weather", "weather forecast", "National Weather Service"]
            
            # Add city names
            for data in weather_data:
                if data.get('city'):
                    keywords.append(f"{data['city']} weather")
                    keywords.append(f"{data['city']} forecast")
            
            # Add weather conditions
            conditions = set()
            for data in weather_data:
                if data.get('forecast') and data['forecast'].get('properties'):
                    periods = data['forecast']['properties']['periods']
                    for period in periods[:2]:  # Just use the first 2 periods
                        condition = period.get('shortForecast', '')
                        if condition:
                            conditions.add(condition)
            
            for condition in list(conditions)[:5]:  # Limit to 5 conditions
                keywords.append(condition)
            
            # Add general weather terms
            keywords.extend(["temperature", "precipitation", "wind", "humidity", "weather alerts"])
            
            return keywords
        except Exception as e:
            logger.error(f"Error generating keywords: {str(e)}")
            # Fallback keywords
            return ["weather forecast", "National Weather Service", f"{zone_name} Zone"]
    
    def _generate_schema_markup(self, zone_name: str, weather_data: List[Dict]) -> Dict:
        """Generate schema markup for the blog post"""
        try:
            # Create the base schema
            schema = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": self._generate_title(zone_name, weather_data),
                "description": self._generate_meta_description(zone_name, weather_data),
                "datePublished": datetime.now().isoformat(),
                "dateModified": datetime.now().isoformat(),
                "author": {
                    "@type": "Organization",
                    "name": "USA Weather Blog"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "USA Weather Blog",
                    "logo": {
                        "@type": "ImageObject",
                        "url": f"{Config.CANONICAL_URL}/logo.png"
                    }
                },
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": f"{Config.CANONICAL_URL}/"
                }
            }
            
            # Add weather forecast schema for each city
            weather_forecasts = []
            for data in weather_data:
                if data.get('city') and data.get('state') and data.get('coordinates'):
                    forecast = {
                        "@type": "WeatherForecast",
                        "name": f"{data['city']}, {data['state']} Weather Forecast",
                        "datePublished": datetime.now().isoformat(),
                        "location": {
                            "@type": "Place",
                            "name": f"{data['city']}, {data['state']}",
                            "geo": {
                                "@type": "GeoCoordinates",
                                "latitude": data['coordinates'][0],
                                "longitude": data['coordinates'][1]
                            }
                        }
                    }
                    
                    # Add forecast summary
                    if data.get('forecast') and data['forecast'].get('properties'):
                        periods = data['forecast']['properties']['periods']
                        if periods:
                            forecast_summary = f"Current conditions: {periods[0].get('shortForecast', 'Variable Conditions')}"
                            if len(periods) > 1:
                                forecast_summary += f". Later: {periods[1].get('shortForecast', 'Variable Conditions')}"
                            forecast["forecast"] = forecast_summary
                    
                    weather_forecasts.append(forecast)
            
            if weather_forecasts:
                schema["about"] = weather_forecasts
            
            # Add FAQ schema
            faqs = self._generate_faqs(weather_data)
            if faqs:
                faq_schema = []
                for faq in faqs:
                    faq_item = {
                        "@type": "Question",
                        "name": faq["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq["answer"]
                        }
                    }
                    faq_schema.append(faq_item)
                
                schema["mainEntity"] = faq_schema
            
            return schema
        except Exception as e:
            logger.error(f"Error generating schema markup: {str(e)}")
            # Fallback schema
            return {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": f"{zone_name} Zone Weather Update",
                "datePublished": datetime.now().isoformat()
            }
    
    def _process_images(self, weather_data: List[Dict]) -> List[Dict]:
        """Process images from the weather data"""
        try:
            images = []
            
            for data in weather_data:
                if data.get('radar_images'):
                    for img in data['radar_images'][:2]:  # Limit to 2 images per city
                        # Convert the image to base64
                        base64_image = self.image_processor.convert_to_base64(img['url'])
                        
                        if base64_image:
                            images.append({
                                'title': img.get('title', 'Weather Radar'),
                                'description': img.get('description', ''),
                                'base64': base64_image,
                                'city': data.get('city', ''),
                                'state': data.get('state', '')
                            })
            
            # Limit the total number of images to avoid exceeding Blogger's limits
            return images[:10]  # Maximum 10 images per post
        except Exception as e:
            logger.error(f"Error processing images: {str(e)}")
            return []
    
    def _generate_related_links(self, zone_name: str, weather_data: List[Dict]) -> List[Dict]:
        """Generate links to related cities and zones"""
        try:
            from zones import get_zone_rotation_order, get_all_cities_in_zone
            
            links = []
            
            # Add links to other zones
            zones = get_zone_rotation_order()
            for zone in zones:
                if zone != zone_name:
                    links.append({
                        'title': f"{zone} Zone Weather",
                        'url': f"{Config.CANONICAL_URL}/zone/{zone.lower().replace(' ', '-')}"
                    })
            
            # Add links to nearby cities (simplified - in production, calculate actual distance)
            for data in weather_data[:5]:  # Limit to 5 cities
                city = data.get('city', '')
                state = data.get('state', '')
                if city and state:
                    links.append({
                        'title': f"{city}, {state} Weather",
                        'url': f"{Config.CANONICAL_URL}/city/{city.lower().replace(' ', '-')}-{state.lower()}"
                    })
            
            return links
        except Exception as e:
            logger.error(f"Error generating related links: {str(e)}")
            return []
    
    def _generate_faqs(self, weather_data: List[Dict]) -> List[Dict]:
        """Generate FAQs based on the weather data"""
        try:
            # Create a prompt for FAQ generation
            prompt = f"""
            Generate 5 frequently asked questions (FAQs) and their answers based on the following weather data:
            
            {json.dumps(weather_data[:3], indent=2)}  # Just use the first 3 cities for brevity
            
            The FAQs should:
            - Be relevant to the current weather conditions
            - Provide helpful information for readers
            - Be concise but informative
            - Cover different aspects of the weather (temperature, precipitation, alerts, etc.)
            
            Format your response as a JSON array of objects, each with "question" and "answer" keys.
            
            Example:
            [
                {
                    "question": "Will it rain today in Boston?",
                    "answer": "Based on the current forecast, there is a 40% chance of rain in Boston this afternoon."
                },
                ...
            ]
            """
            
            # Generate the FAQs
            response = self.model.generate_content(prompt)
            faqs_text = response.text.strip()
            
            # Parse the JSON response
            try:
                faqs = json.loads(faqs_text)
                return faqs
            except json.JSONDecodeError:
                # If the response is not valid JSON, try to extract the FAQs manually
                faqs = []
                lines = faqs_text.split('\n')
                current_question = None
                
                for line in lines:
                    if line.startswith('Q:') or line.startswith('Question:'):
                        current_question = line.replace('Q:', '').replace('Question:', '').strip()
                    elif line.startswith('A:') or line.startswith('Answer:') and current_question:
                        answer = line.replace('A:', '').replace('Answer:', '').strip()
                        faqs.append({
                            'question': current_question,
                            'answer': answer
                        })
                        current_question = None
                
                return faqs
        except Exception as e:
            logger.error(f"Error generating FAQs: {str(e)}")
            # Fallback FAQs
            return [
                {
                    'question': 'What is the current weather trend in this zone?',
                    'answer': 'The current weather trend shows variable conditions across the zone. Please check the detailed forecasts for specific cities.'
                },
                {
                    'question': 'Are there any weather alerts in effect?',
                    'answer': 'There may be weather alerts in some areas. Check the specific city forecasts for the most up-to-date information.'
                }
            ]
    
    def _generate_need_to_know(self, weather_data: List[Dict]) -> List[str]:
        """Generate "What You Need to Know" bullet points"""
        try:
            # Create a prompt for generating need-to-know points
            prompt = f"""
            Generate 5 bullet points for a "What You Need to Know" section based on the following weather data:
            
            {json.dumps(weather_data[:3], indent=2)}  # Just use the first 3 cities for brevity
            
            The bullet points should:
            - Highlight the most important weather information
            - Be concise and easy to understand
            - Focus on practical implications for readers
            - Cover different aspects of the weather (temperature, precipitation, alerts, etc.)
            
            Format your response as a JSON array of strings.
            
            Example:
            [
                "Temperatures will drop after 6 PM",
                "Rainfall expected between 3-7 PM",
                "Winds increase overnight",
                "Tomorrow morning remains cold",
                "Flash flood warning in effect for coastal areas"
            ]
            """
            
            # Generate the bullet points
            response = self.model.generate_content(prompt)
            bullet_points_text = response.text.strip()
            
            # Parse the JSON response
            try:
                bullet_points = json.loads(bullet_points_text)
                return bullet_points
            except json.JSONDecodeError:
                # If the response is not valid JSON, try to extract the bullet points manually
                bullet_points = []
                lines = bullet_points_text.split('\n')
                
                for line in lines:
                    if line.startswith('-') or line.startswith('•'):
                        bullet_point = line.lstrip('- •').strip()
                        if bullet_point:
                            bullet_points.append(bullet_point)
                
                return bullet_points
        except Exception as e:
            logger.error(f"Error generating need-to-know points: {str(e)}")
            # Fallback bullet points
            return [
                "Check local forecasts for the most accurate information",
                "Weather conditions can change rapidly",
                "Follow official sources for weather alerts",
                "Plan outdoor activities accordingly",
                "Stay updated with the latest forecasts"
            ]