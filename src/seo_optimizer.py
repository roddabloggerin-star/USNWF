import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SEOOptimizer:
    def __init__(self):
        pass
    
    def optimize_title(self, title: str, city: str, state: str, main_condition: str) -> str:
        """Optimize the title for SEO and CTR"""
        try:
            current_date = datetime.now().strftime("%B %d")
            current_time = datetime.now().strftime("%I %p").lstrip('0')
            
            # Formula: {City Name} Weather Update: {Strong Hook} ({Month Day}, {Time Range})
            optimized_title = f"{city}, {state} Weather Update: {main_condition} ({current_date}, {current_time})"
            
            # Ensure the title is not too long (Google typically displays 50-60 characters)
            if len(optimized_title) > 60:
                # Truncate the main condition if needed
                max_condition_length = 60 - len(f"{city}, {state} Weather Update:  ({current_date}, {current_time})")
                if max_condition_length > 10:  # Only truncate if we have enough space for a meaningful condition
                    optimized_title = f"{city}, {state} Weather Update: {main_condition[:max_condition_length-3]}... ({current_date}, {current_time})"
                else:
                    # If we don't have enough space, use a shorter format
                    optimized_title = f"{city} Weather: {main_condition[:20]}... ({current_date})"
            
            return optimized_title
        except Exception as e:
            logger.error(f"Error optimizing title: {str(e)}")
            return title
    
    def optimize_meta_description(self, meta_description: str, city: str, state: str) -> str:
        """Optimize the meta description for SEO"""
        try:
            # Ensure the meta description is not too long (Google typically displays 155-160 characters)
            if len(meta_description) > 160:
                meta_description = meta_description[:157] + "..."
            
            # Ensure it contains the city and state for local SEO
            if city not in meta_description or state not in meta_description:
                if len(meta_description) + len(f" {city}, {state}") < 160:
                    meta_description += f" {city}, {state}"
                else:
                    # If we don't have enough space, replace part of the description
                    words = meta_description.split()
                    words.insert(0, f"{city},")
                    if len(" ".join(words)) < 160:
                        meta_description = " ".join(words)
                    else:
                        # If still too long, just add the city at the beginning
                        meta_description = f"{city}, {state} weather forecast and conditions."
            
            return meta_description
        except Exception as e:
            logger.error(f"Error optimizing meta description: {str(e)}")
            return meta_description
    
    def generate_local_authority_signals(self, city: str, state: str, zone_id: int, coordinates: tuple) -> Dict:
        """Generate local authority signals for SEO"""
        try:
            return {
                "updated_using": f"Updated using official NWS data for {city}, {state}.",
                "coordinates": {
                    "latitude": coordinates[0],
                    "longitude": coordinates[1]
                },
                "zone_id": zone_id,
                "micro_regional_context": f"This forecast applies specifically to the {city} area and surrounding regions."
            }
        except Exception as e:
            logger.error(f"Error generating local authority signals: {str(e)}")
            return {}
    
    def generate_internal_links(self, city: str, state: str, zone_name: str) -> Dict:
        """Generate internal links for SEO"""
        try:
            from zones import get_zone_rotation_order, get_all_cities_in_zone
            
            # Link to main USA weather page
            main_weather_link = {
                "title": "USA Weather Today",
                "url": "/usa-weather-today"
            }
            
            # Link to 3 nearest cities (simplified - in production, calculate actual distance)
            zone_cities = get_all_cities_in_zone(zone_name)
            nearby_cities = []
            
            # Find the current city in the list
            current_city_index = None
            for i, c in enumerate(zone_cities):
                if city in c:
                    current_city_index = i
                    break
            
            # Get the cities before and after the current city
            if current_city_index is not None:
                for offset in [-2, -1, 1, 2]:  # Check up to 2 cities before and after
                    index = current_city_index + offset
                    if 0 <= index < len(zone_cities):
                        nearby_city = zone_cities[index]
                        if ", " in nearby_city:
                            city_name, city_state = nearby_city.split(", ", 1)
                            nearby_cities.append({
                                "title": f"{city_name}, {city_state}",
                                "url": f"/city/{city_name.lower().replace(' ', '-')}-{city_state.lower()}"
                            })
            
            # Link to other zones
            other_zones = []
            zones = get_zone_rotation_order()
            for zone in zones:
                if zone != zone_name:
                    other_zones.append({
                        "title": f"{zone} Zone Weather",
                        "url": f"/zone/{zone.lower().replace(' ', '-')}"
                    })
            
            return {
                "main_weather_link": main_weather_link,
                "nearby_cities": nearby_cities[:3],  # Limit to 3 nearby cities
                "other_zones": other_zones
            }
        except Exception as e:
            logger.error(f"Error generating internal links: {str(e)}")
            return {}
    
    def generate_schema_markup(self, blog_post: Dict) -> str:
        """Generate schema markup for the blog post"""
        try:
            import json
            
            # Create the base schema
            schema = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": blog_post.get('title', ''),
                "description": blog_post.get('meta_description', ''),
                "datePublished": blog_post.get('last_updated', ''),
                "dateModified": blog_post.get('last_updated', ''),
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
            
            # Add image schema if images are present
            if blog_post.get('images'):
                images = []
                for img in blog_post['images']:
                    image_schema = {
                        "@type": "ImageObject",
                        "url": f"data:image/jpeg;base64,{img['base64'][:50]}...",  # Just a preview of the base64
                        "caption": img.get('title', ''),
                        "description": img.get('description', '')
                    }
                    images.append(image_schema)
                
                schema["image"] = images
            
            # Add FAQ schema if FAQs are present
            if blog_post.get('faqs'):
                faq_schema = []
                for faq in blog_post['faqs']:
                    faq_item = {
                        "@type": "Question",
                        "name": faq.get('question', ''),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq.get('answer', '')
                        }
                    }
                    faq_schema.append(faq_item)
                
                schema["mainEntity"] = faq_schema
            
            # Add breadcrumb schema
            zone_name = blog_post.get('zone_name', '')
            breadcrumb_schema = {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": f"{Config.CANONICAL_URL}/"
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "USA Weather",
                        "item": f"{Config.CANONICAL_URL}/usa-weather-today"
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": f"{zone_name} Zone",
                        "item": f"{Config.CANONICAL_URL}/zone/{zone_name.lower().replace(' ', '-')}"
                    },
                    {
                        "@type": "ListItem",
                        "position": 4,
                        "name": blog_post.get('title', ''),
                        "item": f"{Config.CANONICAL_URL}/post/{blog_post.get('id', '')}"
                    }
                ]
            }
            
            # Convert schemas to JSON strings
            article_schema_json = json.dumps(schema, indent=2)
            breadcrumb_schema_json = json.dumps(breadcrumb_schema, indent=2)
            
            # Return the schema markup as HTML script tags
            return f"""
            <script type="application/ld+json">
            {article_schema_json}
            </script>
            
            <script type="application/ld+json">
            {breadcrumb_schema_json}
            </script>
            """
        except Exception as e:
            logger.error(f"Error generating schema markup: {str(e)}")
            return ""