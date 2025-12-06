import os
import json
import logging
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import Config

logger = logging.getLogger(__name__)

class BloggerAPI:
    """
    Handles authentication and interaction with the Google Blogger API using OAuth 2.0.
    This implementation is designed for non-interactive environments like GitHub Actions,
    using a pre-generated refresh token.
    """
    def __init__(self):
        self.api_key = Config.BLOGGER_API_KEY
        self.blog_id = Config.BLOGGER_BLOG_ID
        self.service = None
        self.authenticate()

    def authenticate(self):
        """
        Authenticates with the Blogger API using credentials from GitHub Secrets.
        It expects a secret named BLOGGER_CREDENTIALS_JSON containing the
        full credentials object (including refresh_token) as a JSON string.
        """
        try:
            # Get the credentials JSON from environment variables
            creds_json_str = os.environ.get("BLOGGER_CREDENTIALS_JSON")
            if not creds_json_str:
                logger.error("BLOGGER_CREDENTIALS_JSON secret not found.")
                logger.error("Please run the local auth script to generate this secret.")
                return

            # Load the credentials from the JSON string
            creds_info = json.loads(creds_json_str)

            # Create the credentials object
            creds = Credentials.from_authorized_user_info(
                creds_info,
                scopes=['https://www.googleapis.com/auth/blogger']
            )

            # The credentials library will automatically refresh the token if it's expired
            # and a refresh token is available.
            if creds.expired and creds.refresh_token:
                logger.info("Access token expired, refreshing...")
                creds.refresh(Request())
                logger.info("Token refreshed successfully.")

            # Build the service object
            self.service = build('blogger', 'v3', credentials=creds, developerKey=self.api_key)
            logger.info("Successfully authenticated with the Blogger API.")
        except Exception as e:
            logger.error(f"Failed to authenticate with Blogger API: {str(e)}")
            # Do not raise the exception here to allow the script to continue in test mode
            # The main script will handle the failure to publish

    def create_post(self, title: str, content: str, labels: List[str] = None,
                   is_draft: bool = False) -> Optional[Dict]:
        """Create a new blog post."""
        if not self.service:
            logger.error("Blogger service not initialized. Cannot create post.")
            return None

        try:
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
        """Get recent posts from the blog."""
        if not self.service:
            logger.error("Blogger service not initialized. Cannot get posts.")
            return []
        try:
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
        """Update an existing blog post."""
        if not self.service:
            logger.error("Blogger service not initialized. Cannot update post.")
            return None
        try:
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
        """Delete a blog post."""
        if not self.service:
            logger.error("Blogger service not initialized. Cannot delete post.")
            return False
        try:
            self.service.posts().delete(
                blogId=self.blog_id,
                postId=post_id
            ).execute()
            logger.info(f"Successfully deleted post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete post: {str(e)}")
            return False