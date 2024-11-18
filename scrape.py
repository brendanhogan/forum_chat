import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class StyleForumScraper:
    def __init__(self, thread_url):
        self.thread_url = thread_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        self.posts = []
        
    def get_page_content(self, page_num):
        """Fetch content from a specific page number"""
        if page_num == 1:
            url = self.thread_url
        else:
            url = f"{self.thread_url}page-{page_num}"
            
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching page {page_num}: {str(e)}")
            return None

    def parse_post(self, post_element):
        """Extract information from a single post"""
        try:
            # Get post content using the correct class selector
            message_content = post_element.find('div', class_='message-userContent')
            if not message_content:
                return None
                
            # Get the actual text content, removing unnecessary whitespace
            post_text = message_content.get_text(separator='\n', strip=True)
            
            # Get post date
            post_date = post_element.find('time')
            if post_date:
                post_date = post_date.get('datetime', '')
            
            # Get username
            username = post_element.find('h4', class_='message-name')
            if username:
                username = username.get_text(strip=True)
                
            # Get post number
            post_number = post_element.find('a', class_='message-number')
            if post_number:
                post_number = post_number.get_text(strip=True).replace('#', '')
            
            return {
                'post_number': post_number,
                'username': username,
                'date': post_date,
                'content': post_text
            }
            
        except Exception as e:
            print(f"Error parsing post: {str(e)}")
            return None

    def scrape_thread(self, start_page=1, end_page=None):
        """Scrape the entire thread"""
        current_page = start_page
        
        while True:
            print(f"Scraping page {current_page}...")
            html_content = self.get_page_content(current_page)
            
            if not html_content:
                break
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all posts on the page
            posts = soup.find_all('article', class_='message')
            
            if not posts:
                break
                
            for post in posts:
                post_data = self.parse_post(post)
                if post_data:
                    self.posts.append(post_data)
            
            # Check if we've reached the end page
            if end_page and current_page >= end_page:
                break
                
            # Check for next page
            pagination = soup.find('nav', class_='pageNavWrapper')
            if not pagination or not pagination.find('a', class_='pageNav-jump--next'):
                break
                
            current_page += 1
            time.sleep(2)  # Be nice to the server
    
    def save_to_file(self, output_file="forum_data.json"):
        """Save scraped data to a JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'thread_url': self.thread_url,
                'scrape_date': datetime.now().isoformat(),
                'posts': self.posts
            }, f, indent=2, ensure_ascii=False)
        
        # Also save a text-only version for easier processing
        with open('forum_data.txt', 'w', encoding='utf-8') as f:
            for post in self.posts:
                f.write(f"Post #{post['post_number']} by {post['username']} on {post['date']}\n")
                f.write(f"{post['content']}\n")
                f.write("-" * 80 + "\n\n")

def main():
    thread_url = "https://www.styleforum.net/threads/s-e-h-kelly.277070/"
    scraper = StyleForumScraper(thread_url)
    
    scraper.scrape_thread(start_page=1, end_page=400)
    
    # Save the results
    scraper.save_to_file()
    print(f"Scraped {len(scraper.posts)} posts successfully!")

if __name__ == "__main__":
    main()