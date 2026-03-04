"""
Advanced Substack Post Downloader
With options for format, filtering, and more
"""

import json
import os
import re
import argparse
import urllib.request
import urllib.error
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def clean_filename(title):
    """Convert title to safe filename"""
    filename = re.sub(r'[^\w\s-]', '', title)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename[:50].strip('-')

def html_to_markdown(html):
    """Basic HTML to markdown conversion"""
    text = re.sub(r'<[^>]+>', '', html)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    return text.strip()

def fetch_url(url, accept='*/*'):
    """Fetch a URL with browser-like headers"""
    headers = {**HEADERS, 'Accept': accept}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()

def fetch_posts_via_api(base_url, limit=None):
    """Fetch posts using Substack's JSON API (bypasses Cloudflare RSS blocking)"""
    posts = []
    offset = 0
    batch_size = 12

    while True:
        api_url = f"{base_url}/api/v1/archive?sort=new&offset={offset}&limit={batch_size}"
        print(f"  Fetching batch at offset {offset}...")
        data = json.loads(fetch_url(api_url, accept='application/json'))

        if not data:
            break

        posts.extend(data)
        offset += batch_size

        if limit and len(posts) >= limit:
            posts = posts[:limit]
            break

        if len(data) < batch_size:
            break

    return posts

def fetch_post_content(base_url, slug):
    """Fetch full post content from the API"""
    url = f"{base_url}/api/v1/posts/{slug}"
    data = json.loads(fetch_url(url, accept='application/json'))
    return data.get('body_html', '') or data.get('body', '') or ''

def download_posts(base_url, output_dir='substack_posts', limit=None, force=False):
    """Download posts from Substack"""
    print(f"📡 Fetching posts from {base_url}...")

    try:
        posts = fetch_posts_via_api(base_url, limit)
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")
        return

    if not posts:
        print("❌ No posts found")
        return

    print(f"✓ Found {len(posts)} posts\n")

    os.makedirs(output_dir, exist_ok=True)

    new_count = 0
    skipped_count = 0
    updated_count = 0

    for post in posts:
        title = post.get('title', 'Untitled')
        slug = post.get('slug', '')
        published = post.get('post_date', 'Unknown date')
        link = post.get('canonical_url', f"{base_url}/p/{slug}")

        filename = f"{clean_filename(title)}.md"
        filepath = os.path.join(output_dir, filename)

        file_existed = os.path.exists(filepath)

        if file_existed and not force:
            print(f"⏭️  Skipped: {filename} (use --force to overwrite)")
            skipped_count += 1
            continue

        # Fetch full post content
        try:
            body_html = fetch_post_content(base_url, slug)
            content = html_to_markdown(body_html) if body_html else "No content available"
        except Exception:
            content = html_to_markdown(post.get('description', '')) or "No content available"

        markdown = f"""# {title}

**Published:** {published}
**Link:** {link}

---

{content}
"""

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)

            if file_existed:
                print(f"🔄 Updated: {filename}")
                updated_count += 1
            else:
                print(f"✓ Saved: {filename}")
                new_count += 1
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")

    # Summary
    print(f"\n{'='*50}")
    print(f"✓ New posts: {new_count}")
    if updated_count > 0:
        print(f"🔄 Updated: {updated_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"📁 Location: {os.path.abspath(output_dir)}/")
    print(f"{'='*50}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download Substack posts')
    parser.add_argument('--url', default='https://takschdube.substack.com',
                       help='Substack publication URL (e.g. https://yourname.substack.com)')
    parser.add_argument('--output', default='substack_posts',
                       help='Output directory')
    parser.add_argument('--limit', type=int,
                       help='Limit number of posts to download')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite existing files')

    args = parser.parse_args()

    # Strip trailing /feed or / from URL for API usage
    base_url = args.url.rstrip('/')
    if base_url.endswith('/feed'):
        base_url = base_url[:-5]

    print("🚀 Substack Post Downloader\n")
    download_posts(base_url, args.output, args.limit, args.force)
    print("\n✨ Done!")
