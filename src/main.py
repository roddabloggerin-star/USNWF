import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from config import Config
from nws_api import NWSAPI
from blogger_api import BloggerAPI
from content_generator import ContentGenerator
from zones import get_zone_rotation_order

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("weather_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the weather bot"""
    try:
        logger.info("Starting weather bot")
        
        # Initialize components
        nws_api = NWSAPI()
        content_generator = ContentGenerator()
        
        # Initialize Blogger API only if we're publishing
        blogger_api = None
        if Config.PUBLISH_TO_BLOGGER:
            blogger_api = BloggerAPI()
        
        # Get the current zone to process (rotate through zones)
        zones = get_zone_rotation_order()
        current_hour = datetime.now().hour
        zone_index = current_hour % len(zones)
        current_zone = zones[zone_index]
        
        logger.info(f"Processing zone: {current_zone}")
        
        # Get weather data for the current zone
        logger.info("Fetching weather data...")
        weather_data = nws_api.get_zone_weather_data(current_zone)
        
        if not weather_data:
            logger.error(f"No weather data available for zone: {current_zone}")
            return
        
        logger.info(f"Retrieved weather data for {len(weather_data)} cities in {current_zone}")
        
        # Generate the blog post
        logger.info("Generating blog post...")
        blog_post = content_generator.generate_blog_post(current_zone, weather_data)
        
        if not blog_post:
            logger.error("Failed to generate blog post")
            return
        
        logger.info(f"Generated blog post with {blog_post['word_count']} words")
        
        # Format the blog post as HTML
        logger.info("Formatting blog post as HTML...")
        html_content = format_blog_post_as_html(blog_post)
        
        # Save the blog post locally (for testing or backup)
        logger.info("Saving blog post locally...")
        save_blog_post_locally(blog_post, html_content)
        
        # Publish to Blogger if configured
        if Config.PUBLISH_TO_BLOGGER and blogger_api:
            logger.info("Publishing to Blogger...")
            labels = [current_zone, "weather", "forecast", "NWS"]
            labels.extend(blog_post['keywords'][:5])  # Add up to 5 keywords as labels
            
            post = blogger_api.create_post(
                title=blog_post['title'],
                content=html_content,
                labels=labels
            )
            
            if post:
                logger.info(f"Successfully published blog post: {post.get('url')}")
            else:
                logger.error("Failed to publish blog post")
        else:
            logger.info("Test mode: Blog post saved locally but not published")
        
        logger.info("Weather bot completed successfully")
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise

def format_blog_post_as_html(blog_post: Dict) -> str:
    """Format the blog post as HTML"""
    try:
        # Start with the schema markup
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{blog_post['title']}</title>
            <meta name="description" content="{blog_post['meta_description']}">
            <meta name="keywords" content="{', '.join(blog_post['keywords'])}">
            <meta name="author" content="USA Weather Blog">
            
            <!-- Open Graph meta tags -->
            <meta property="og:title" content="{blog_post['title']}">
            <meta property="og:description" content="{blog_post['meta_description']}">
            <meta property="og:type" content="article">
            <meta property="og:url" content="{Config.CANONICAL_URL}/">
            
            <!-- Twitter Card meta tags -->
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:title" content="{blog_post['title']}">
            <meta name="twitter:description" content="{blog_post['meta_description']}">
            
            <!-- Canonical URL -->
            <link rel="canonical" href="{Config.CANONICAL_URL}/">
            
            <!-- Google Analytics -->
            <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
            <script>
                window.dataLayer = window.dataLayer || [];
                function gtag(){{dataLayer.push(arguments);}}
                gtag('js', new Date());
                gtag('config', 'GA_MEASUREMENT_ID');
            </script>
            
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .weather-card {{
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .need-to-know {{
                    background-color: #e9f7fe;
                    border-left: 4px solid #3498db;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .faq {{
                    margin-bottom: 20px;
                }}
                .faq-question {{
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .related-links {{
                    margin-top: 30px;
                }}
                .related-links a {{
                    display: inline-block;
                    margin-right: 10px;
                    margin-bottom: 10px;
                    background-color: #3498db;
                    color: white;
                    padding: 8px 12px;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 20px 0;
                }}
                .disclaimer {{
                    margin-top: 40px;
                    padding: 15px;
                    background-color: #f5f5f5;
                    border-left: 4px solid #ccc;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            {blog_post['schema_markup']}
            
            <h1>{blog_post['title']}</h1>
            
            <div class="need-to-know">
                <h2>What You Need to Know</h2>
                <ul>
        """
        
        # Add "What You Need to Know" bullet points
        for point in blog_post['need_to_know']:
            html += f"                    <li>{point}</li>\n"
        
        html += """
                </ul>
            </div>
        """
        
        # Add images
        if blog_post.get('images'):
            html += "<div class='weather-images'>\n"
            for img in blog_post['images']:
                html += f"""
                <figure>
                    <img src="data:image/jpeg;base64,{img['base64']}" alt="{img['title']}">
                    <figcaption>{img['description']} - {img['city']}, {img['state']}</figcaption>
                </figure>
                """
            html += "</div>\n"
        
        # Add the main content
        html += f"""
            <div class="weather-content">
                {blog_post['content']}
            </div>
        """
        
        # Add FAQs
        if blog_post.get('faqs'):
            html += "<div class='faq-section'>\n<h2>Frequently Asked Questions</h2>\n"
            for faq in blog_post['faqs']:
                html += f"""
                <div class='faq'>
                    <div class='faq-question'>{faq['question']}</div>
                    <div class='faq-answer'>{faq['answer']}</div>
                </div>
                """
            html += "</div>\n"
        
        # Add related links
        if blog_post.get('related_links'):
            html += "<div class='related-links'>\n<h2>Related Weather Information</h2>\n"
            for link in blog_post['related_links']:
                html += f"<a href='{link['url']}'>{link['title']}</a>\n"
            html += "</div>\n"
        
        # Add the disclaimer (already included in content, but adding again for emphasis)
        html += """
            <div class="disclaimer">
                <p><strong>Disclaimer:</strong> This post is created using the public data provided by the National Weather Service. Please check the <a href="https://www.weather.gov/" target="_blank">Original source</a> for more information.</p>
            </div>
        """
        
        # Close HTML tags
        html += """
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        logger.error(f"Error formatting blog post as HTML: {str(e)}")
        raise

def save_blog_post_locally(blog_post: Dict, html_content: str):
    """Save the blog post locally for testing or backup"""
    try:
        # Create a directory for blog posts if it doesn't exist
        os.makedirs("blog_posts", exist_ok=True)
        
        # Create a filename based on the zone and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zone_name = blog_post.get('zone_name', 'unknown').replace(' ', '_').lower()
        filename = f"blog_posts/{zone_name}_{timestamp}.html"
        
        # Save the HTML content
        with open(filename, 'w') as f:
            f.write(html_content)
        
        # Save the blog post data as JSON
        json_filename = f"blog_posts/{zone_name}_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(blog_post, f, indent=2)
        
        logger.info(f"Saved blog post locally: {filename}")
    except Exception as e:
        logger.error(f"Error saving blog post locally: {str(e)}")

if __name__ == "__main__":
    main()