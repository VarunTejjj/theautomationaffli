# blogger.py

import time
import requests
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, BLOGGER_BLOG_ID

# To enable admin notification, import below in your bot.py and assign to this after bot is initialized:
notify_token_refresh = None

_cached_token = None
_token_acquired_time = 0
_TOKEN_EXPIRE_INTERVAL = 40 * 60  # 40 minutes (in seconds)


def refresh_access_token():
    """
    Refresh and cache the access token using the refresh token, auto-refreshing every 40 minutes.
    If notify_token_refresh is set, it will be called each time a new token is acquired (e.g. to message admin).
    """
    global _cached_token, _token_acquired_time
    current_time = time.time()
    if _cached_token and (current_time - _token_acquired_time) < _TOKEN_EXPIRE_INTERVAL:
        return _cached_token

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
        _cached_token = tokens["access_token"]
        _token_acquired_time = current_time
        print(f"Access token refreshed at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
        if notify_token_refresh:
            try:
                notify_token_refresh()
            except Exception:
                # Silently ignore notification errors to avoid breaking refresh
                pass
        return _cached_token
    else:
        raise Exception(f"Failed to refresh access token: {response.text}")


def create_post(title, content, image_url, button_url):
    """
    Create a new blog post on Blogger, using a fresh access token
    and sending admin notification when token is refreshed.
    """
    access_token = refresh_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    blog_post = {
        "kind": "blogger#post",
        "blog": {"id": BLOGGER_BLOG_ID},
        "title": title,
        "content": f'''
            <img src="{image_url}" alt="{title}"><br><br>
            <p>{content}</p><br>
            <a href="{button_url}" style="
                display:inline-block; padding:10px 20px;
                background:#4285F4; color:#fff;
                text-decoration:none; border-radius:4px;
                font-weight:bold;">View in Bot</a>
        '''
    }
    endpoint = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/"
    response = requests.post(endpoint, headers=headers, json=blog_post)
    if response.status_code in (200, 201):
        return response.json().get("url", "")
    else:
        raise Exception(f"Blogger API Error {response.status_code}: {response.text}")
