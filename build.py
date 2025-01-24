import os
import markdown
import shutil
import yaml
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Load templates
env = Environment(loader=FileSystemLoader('templates'))
index_template = env.get_template('index.html')
post_template = env.get_template('post.html')

# Copy static files
def copy_static_files():
    static_dir = 'static'
    output_static_dir = 'production/static'

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
    def __init__(self, title, date, tags, slug, content):
        self.title = title
        self.date = date
        self.tags = tags
        self.slug = slug
        self.content = content

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
                    slug=slug,
                    content=post_content
                )
                posts.append(post)
    posts.sort(key=lambda post: datetime.strptime(post.date, "%Y-%m-%d"), reverse=True)
    return posts

# Generate index page
def generate_index(posts):
    output_path = 'production/index.html'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(index_template.render(posts=posts))

# Generate individual post pages
def generate_posts(posts):
    for post in posts:
        output_path = f'production/posts/{post.slug}.html'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(post_template.render(post=post))

def main():
    copy_static_files()
    posts = load_posts()
    generate_index(posts)
    generate_posts(posts)
    print("Site generated in 'production/' directory.")

if __name__ == "__main__":
    main()

