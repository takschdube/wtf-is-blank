"""
Advanced Substack Post Downloader
With options for format, filtering, and more
"""

import feedparser
import os
import re
import argparse
import urllib.request
from datetime import datetime

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

def download_posts(feed_url, output_dir='substack_posts', limit=None, force=False):
    """Download posts from Substack RSS feed"""
    print(f"📡 Fetching posts from {feed_url}...")
    
    try:
        req = urllib.request.Request(feed_url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SubstackPostDownloader/1.0)'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            feed_content = response.read()
        feed = feedparser.parse(feed_content)
    except Exception as e:
        print(f"❌ Error fetching feed: {e}")
        return
    
    if not feed.entries:
        print("❌ No posts found in feed")
        return
    
    total_posts = len(feed.entries)
    if limit:
        total_posts = min(total_posts, limit)
        feed.entries = feed.entries[:limit]
    
    print(f"✓ Found {total_posts} posts\n")
    
    os.makedirs(output_dir, exist_ok=True)
    
    new_count = 0
    skipped_count = 0
    updated_count = 0
    
    for i, entry in enumerate(feed.entries, 1):
        title = entry.title
        published = entry.get('published', 'Unknown date')
        link = entry.link
        
        if hasattr(entry, 'content'):
            content = entry.content[0].value
        elif hasattr(entry, 'summary'):
            content = entry.summary
        else:
            content = "No content available"
        
        content = html_to_markdown(content)
        
        filename = f"{clean_filename(title)}.md"
        filepath = os.path.join(output_dir, filename)

        markdown = f"""# {title}

**Published:** {published}
**Link:** {link}

---

{content}
"""

        # Check if file exists before writing
        file_existed = os.path.exists(filepath)

        if file_existed and not force:
            print(f"⏭️  Skipped: {filename} (use --force to overwrite)")
            skipped_count += 1
            continue

        # Save file
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
    parser.add_argument('--url', default='https://takschdube.substack.com/feed',
                       help='Substack RSS feed URL')
    parser.add_argument('--output', default='substack_posts',
                       help='Output directory')
    parser.add_argument('--limit', type=int,
                       help='Limit number of posts to download')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite existing files')
    
    args = parser.parse_args()
    
    print("🚀 Substack Post Downloader\n")
    download_posts(args.url, args.output, args.limit, args.force)
    print("\n✨ Done!")