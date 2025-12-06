import requests
import json
import base64
import logging
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import Config

logger = logging.getLogger(__name__)

class BloggerAPI:
    def __init__(self):
        self.api_key = Config.BLOGGER_API_KEY
        self.blog_id = Config.BLOGGER_BLOG_ID
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Blogger API"""
        try:
            # In a real implementation, you would use OAuth2 with credentials stored in GitHub Secrets
            # For simplicity, this is a placeholder for the authentication process
            # In production, you would:
            # 1. Store OAuth2 credentials in GitHub Secrets
            # 2. Use those credentials to authenticate
            # 3. Build the service object
            
            # This is a placeholder - replace with actual OAuth2 flow
            self.service = build('blogger', 'v3', developerKey=self.api_key)
            logger.info("Successfully authenticated with Blogger API")
        except Exception as e:
            logger.error(f"Failed to authenticate with Blogger API: {str(e)}")
            raise
    
    def create_post(self, title: str, content: str, labels: List[str] = None, 
                   is_draft: bool = False) -> Optional[Dict]:
        """Create a new blog post"""
        try:
            if not self.service:
                logger.error("Blogger service not initialized")
                return None
            
            post_body = {
                'title': title,
                'content': content,
                'labels': labels or [],
                'isDraft': is_draft
            }
            
            post = self.service.posts().insert(
                blogId=self.blog_id,
                body=post_body
            ).execute()
            
            logger.info(f"Successfully created post: {post.get('url')}")
            return post
        except Exception as e:
            logger.error(f"Failed to create post: {str(e)}")
            return None
    
    def get_posts(self, max_results: int = 10) -> List[Dict]:
        """Get recent posts from the blog"""
        try:
            if not self.service:
                logger.error("Blogger service not initialized")
                return []
            
            posts = self.service.posts().list(
                blogId=self.blog_id,
                maxResults=max_results
            ).execute()
            
            return posts.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get posts: {str(e)}")
            return []
    
    def update_post(self, post_id: str, title: str = None, content: str = None, 
                   labels: List[str] = None) -> Optional[Dict]:
        """Update an existing blog post"""
        try:
            if not self.service:
                logger.error("Blogger service not initialized")
                return None
            
            # Get the current post
            post = self.service.posts().get(
                blogId=self.blog_id,
                postId=post_id
            ).execute()
            
            # Update fields if provided
            if title:
                post['title'] = title
            if content:
                post['content'] = content
            if labels:
                post['labels'] = labels
            
            updated_post = self.service.posts().update(
                blogId=self.blog_id,
                postId=post_id,
                body=post
            ).execute()
            
            logger.info(f"Successfully updated post: {updated_post.get('url')}")
            return updated_post
        except Exception as e:
            logger.error(f"Failed to update post: {str(e)}")
            return None
    
    def delete_post(self, post_id: str) -> bool:
        """Delete a blog post"""
        try:
            if not self.service:
                logger.error("Blogger service not initialized")
                return False
            
            self.service.posts().delete(
                blogId=self.blog_id,
                postId=post_id
            ).execute()
            
            logger.info(f"Successfully deleted post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete post: {str(e)}")
            return False