# blogger.py

import requests
from config import BLOGGER_BLOG_ID, BLOGGER_OAUTH_TOKEN

def create_post(title, content, image_url, button_url):
    """Create a new Blogger post for a product."""
    headers = {
        "Authorization": f"Bearer {BLOGGER_OAUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "kind": "blogger#post",
        "blog": {"id": BLOGGER_BLOG_ID},
        "title": title,
        "content": f'''
        <img src="{image_url}"><br>
        <p>{content}</p>
        <a href="{button_url}" style="display:inline-block;padding:10px 20px;background:#007bff;color:#fff;border-radius:5px;text-decoration:none;">View in Bot</a>
        '''
    }
    response = requests.post(
        f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/",
        headers=headers,
        json=body
    )
    if response.status_code == 200 or response.status_code == 201:
        post = response.json()
        return post["url"]
    else:
        raise Exception(f"Blogger API error: {response.status_code} - {response.text}")
