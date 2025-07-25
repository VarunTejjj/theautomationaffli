# blogger.py

import requests
from config import BLOGGER_BLOG_ID, BLOGGER_OAUTH_TOKEN

def create_post(title, content, image_url, button_url):
    """Create a new blog post in Blogger."""
    headers = {
        "Authorization": f"Bearer {BLOGGER_OAUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    post_body = {
        "kind": "blogger#post",
        "blog": {"id": BLOGGER_BLOG_ID},
        "title": title,
        "content": f'''
            <img src="{image_url}" alt="{title}"><br><br>
            <p>{content}</p><br>
            <a href="{button_url}" style="
              display:inline-block;
              padding:10px 20px;
              background:#4285F4;
              color:#fff;
              text-decoration:none;
              border-radius:4px;
              font-weight:bold;
            ">View in Bot</a>
        '''
    }
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/"
    response = requests.post(url, headers=headers, json=post_body)

    if response.status_code in (200, 201):
        post_data = response.json()
        return post_data.get("url", "")
    else:
        raise Exception(f"Blogger API Error {response.status_code}: {response.text}")
