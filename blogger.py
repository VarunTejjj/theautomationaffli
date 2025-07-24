# blogger.py

from google_auth import get_blogger_service

BLOG_ID = 'YOUR_BLOGGER_BLOG_ID_HERE'  # Replace with your Blogger blog ID

def create_post(title, content, labels=None):
    service = get_blogger_service()

    body = {
        'kind': 'blogger#post',
        'title': title,
        'content': content,
        'labels': labels or []
    }

    post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
    return post.get('url')
