import os
import markdown
import shutil
import yaml
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Load templates
env = Environment(loader=FileSystemLoader('templates'))
index_template = env.get_template('index.html')
technical_template = env.get_template('technical.html')
post_template = env.get_template('post.html')

# site configuration
SITE_URL = "https://jacksoncrowley.xyz"

# Copy static files
def copy_static_files():
    static_dir = 'static'
    output_static_dir = 'docs/static'

    # Create output static directory if it doesn't exist
    if not os.path.exists(output_static_dir):
        os.makedirs(output_static_dir)

    # Copy static files (CSS, images, etc.)
    for file_name in os.listdir(static_dir):
        static_file_path = os.path.join(static_dir, file_name)
        if os.path.isfile(static_file_path):
            shutil.copy(static_file_path, output_static_dir)

# Define post structure
class Post:
    def __init__(self, title, date, description, tags, slug, content):
        self.title = title
        self.date = date
        self.description = description
        self.tags = tags
        self.slug = slug
        self.content = content
        self.canonical_url = f"{SITE_URL}/posts/{slug}/"

# Parse Markdown files in 'posts/' directory
def load_posts():
    posts = []
    for filename in os.listdir('posts'):
        if filename.endswith('.md'):
            with open(os.path.join('posts', filename), 'r') as f:
                content = f.read()
                
                # Split YAML front matter and body content
                front_matter, body = content.split('---\n', 2)[1:]
                post_data = yaml.safe_load(front_matter)
                post_content = markdown.markdown(body, extensions=["footnotes", "fenced_code", "toc"])
                slug = os.path.splitext(filename)[0]
                post = Post(
                    title=post_data['title'],
                    date=post_data['date'],
                    tags=post_data.get('tags', []),
                    description=post_data.get('description', ''),
                    slug=slug,
                    content=post_content
                )
                posts.append(post)
    posts.sort(key=lambda post: datetime.strptime(post.date, "%Y-%m-%d"), reverse=True)
    return posts

# Generate index page
def generate_index():
    output_path = 'docs/index.html'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(index_template.render())

# Generate technical page
def generate_technical(posts):
    output_path = 'docs/technical.html'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(technical_template.render(posts=posts))


# Generate individual post pages
def generate_posts(posts):
    for post in posts:
        output_path = f'docs/posts/{post.slug}.html'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(post_template.render(post=post))

# Generate sitemap
def generate_sitemap(posts):
    sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>',
                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    
    # Add homepage
    sitemap_content.extend([
        '  <url>',
        f'    <loc>{SITE_URL}/</loc>',
        '    <changefreq>weekly</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>'
    ])
    
    # Add technical page
    sitemap_content.extend([
        '  <url>',
        f'    <loc>{SITE_URL}/technical.html</loc>',
        '    <changefreq>weekly</changefreq>',
        '    <priority>0.8</priority>',
        '  </url>'
    ])
    
    # Add all posts
    for post in posts:
        sitemap_content.extend([
            '  <url>',
            f'    <loc>{post.canonical_url}</loc>',
            f'    <lastmod>{post.date}</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.6</priority>',
            '  </url>'
        ])
    
    sitemap_content.append('</urlset>')
    
    with open('docs/sitemap.xml', 'w') as f:
        f.write('\n'.join(sitemap_content))

def main():
    copy_static_files()
    posts = load_posts()
    generate_index()
    generate_technical(posts)
    generate_posts(posts)
    generate_sitemap(posts)
    print("Site generated in 'docs/' directory.")

if __name__ == "__main__":
    main()

