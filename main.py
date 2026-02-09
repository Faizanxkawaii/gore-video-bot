import json
import time
import os
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# Site configurations with selectors
SITES = {
    'DeepGoreTube': {
        'url': 'https://deepgoretube.site/',
        'video_selector': '.video',
        'title_selector': 'h2',
        'link_selector': 'a',
        'base_url': 'https://deepgoretube.site'
    },
    'GoreCenter': {
        'url': 'https://www.gorecenter.com/',
        'video_selector': '.video-card',
        'title_selector': '.video-title',
        'link_selector': 'a',
        'base_url': 'https://www.gorecenter.com'
    },
    'BestGore': {
        'url': 'https://bestgore.fun/videos/recently-added',
        'video_selector': '.video-item',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://bestgore.fun'
    },
    'CrazyShit': {
        'url': 'https://crazyshit.com/',
        'video_selector': '.thumb',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://crazyshit.com'
    },
    'GoreSee': {
        'url': 'https://goresee.com/videos/browse',
        'video_selector': '.video-item',
        'title_selector': '.video-title',
        'link_selector': 'a',
        'base_url': 'https://goresee.com'
    },
    'SeeGore': {
        'url': 'https://seegore.com/gore/',
        'video_selector': '.post',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://seegore.com'
    },
    'AliveGore': {
        'url': 'https://alivegore.com/',
        'video_selector': '.video',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://alivegore.com'
    },
    'WatchPeopleDie': {
        'url': 'https://watchpeopledie.tv/',
        'video_selector': '.video-card',
        'title_selector': '.video-title',
        'link_selector': 'a',
        'base_url': 'https://watchpeopledie.tv'
    },
    'E-Fukt': {
        'url': 'https://efukt.com/',
        'video_selector': '.video',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://efukt.com'
    },
    'Kaotic': {
        'url': 'https://kaotic.com/',
        'video_selector': '.video-item',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://kaotic.com'
    }
}

class VideoScraperBot:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.database_file = 'videos_database.json'
        self.database = self.load_database()
        self.driver = None
    
    def load_database(self):
        """Load videos database from JSON file"""
        if os.path.exists(self.database_file):
            try:
                with open(self.database_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading database: {e}")
                return {'sent_videos': []}
        return {'sent_videos': []}
    
    def save_database(self):
        """Save videos database to JSON file"""
        try:
            with open(self.database_file, 'w') as f:
                json.dump(self.database, f, indent=2)
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def is_video_sent(self, video_url):
        """Check if video URL already sent"""
        return any(v.get('url') == video_url for v in self.database.get('sent_videos', []))
    
    def add_video_to_db(self, site, title, url):
        """Add video to database"""
        self.database.setdefault('sent_videos', []).append({
            'site': site,
            'title': title,
            'url': url,
            'added_at': datetime.now().isoformat()
        })
    
    def setup_driver(self):
        """Setup Selenium WebDriver with headless Chrome"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service('/usr/local/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            return True
        except Exception as e:
            print(f"Failed to setup Chrome driver: {e}")
            return False
    
    def scrape_site(self, site_name, config):
        """Scrape videos from a single site using Selenium"""
        videos = []
        count = 0
        
        try:
            if not self.driver:
                if not self.setup_driver():
                    print(f"Failed to setup driver for {site_name}")
                    return []
            
            print(f"Scraping {site_name}...")
            self.driver.get(config['url'])
            time.sleep(3)  # Wait for page to load
            
            # Find video elements
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, config['video_selector'])
            
            for video_elem in video_elements[:20]:  # Limit to first 20
                try:
                    # Get title
                    try:
                        title_elem = video_elem.find_element(By.CSS_SELECTOR, config['title_selector'])
                        title = title_elem.text.strip()
                    except NoSuchElementException:
                        title = "No title"
                    
                    # Get link
                    try:
                        link_elem = video_elem.find_element(By.CSS_SELECTOR, config['link_selector'])
                        href = link_elem.get_attribute('href')
                    except NoSuchElementException:
                        continue
                    
                    if href and title and title != "No title":
                        # Make absolute URL if relative
                        if href.startswith('/'):
                            href = config['base_url'] + href
                        
                        if not self.is_video_sent(href):
                            videos.append({
                                'title': title,
                                'url': href,
                                'site': site_name
                            })
                            count += 1
                except Exception as e:
                    print(f"Error processing video in {site_name}: {e}")
                    continue
            
            print(f"Found {count} new videos from {site_name}")
            return videos
            
        except WebDriverException as e:
            print(f"WebDriver error scraping {site_name}: {e}")
            return []
        except Exception as e:
            print(f"Error scraping {site_name}: {e}")
            return []
    
    async def send_telegram_message(self, site, title, url):
        """Send message to Telegram chat"""
        try:
            bot = Bot(token=self.bot_token)
            message = (
                f"🔥 Naya Video Aaya Hai!\n"
                f"🌐 Source: {site}\n"
                f"📌 Title: {title}\n"
                f"🔗 Watch Now: {url}"
            )
            await bot.send_message(chat_id=self.chat_id, text=message)
            print(f"Sent Telegram message for: {title}")
            return True
        except TelegramError as e:
            print(f"Telegram error: {e}")
            return False
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    async def run(self):
        """Main execution method"""
        print("Starting video scraper bot...")
        
        # Initialize bot
        try:
            bot = Bot(token=self.bot_token)
            await bot.get_me()
            print("Telegram bot connected successfully")
        except Exception as e:
            print(f"Failed to connect to Telegram: {e}")
            return
        
        all_videos = []
        
        # Scrape all sites
        for site_name, config in SITES.items():
            videos = self.scrape_site(site_name, config)
            all_videos.extend(videos)
            time.sleep(2)  # Rate limiting between sites
        
        # Send new videos to Telegram
        sent_count = 0
        for video in all_videos:
            if not video.get('telegram_sent', False):
                success = await self.send_telegram_message(
                    video['site'],
                    video['title'],
                    video['url']
                )
                if success:
                    video['telegram_sent'] = True
                    video['sent_at'] = datetime.now().isoformat()
                    self.add_video_to_db(video['site'], video['title'], video['url'])
                    sent_count += 1
                    time.sleep(1)  # Rate limiting between messages
        
        # Save database
        self.save_database()
        
        # Quit driver
        if self.driver:
            self.driver.quit()
        
        print(f"\nCompleted! Total new videos found: {len(all_videos)}")
        print(f"Videos sent to Telegram: {sent_count}")

if __name__ == '__main__':
    # Get credentials from environment variables
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7911359291:AAFIFlS55_aLnXp00zfukZQjzGhhh0kUY8I')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5412212545')
    
    bot = VideoScraperBot(BOT_TOKEN, CHAT_ID)
    asyncio.run(bot.run())
