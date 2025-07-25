# blogger.py

import requests
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, BLOGGER_BLOG_ID

def refresh_access_token():
    """Use the refresh token to get a new access token."""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        return tokens["access_token"]
    else:
        raise Exception(f"Failed to refresh access token: {response.text}")

def create_post(title, content, image_url, button_url):
    """Create a new blog post on Blogger using a fresh access token."""
    access_token = refresh_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    blog_post = {
        "kind": "blogger#post",
        "blog": {"id": BLOGGER_BLOG_ID},
        "title": title,
        "content": f'''
            <img src="{image_url}" alt="{title}"><br><br>
            <p>{content}</p><br>
            <a href="{button_url}" style="
                display:inline-block;padding:10px 20px;
                background:#4285F4;color:#fff;
                text-decoration:none;border-radius:4px;
                font-weight:bold;">View in Bot</a>
        '''
    }
    endpoint = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/"
    response = requests.post(endpoint, headers=headers, json=blog_post)

    if response.status_code in (200, 201):
        return response.json().get("url", "")
    else:
        raise Exception(f"Blogger API Error {response.status_code}: {response.text}")
