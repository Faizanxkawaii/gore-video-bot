import json
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Bot
from telegram.error import TelegramError

# Site configurations with selectors
SITES = {
    'DeepGoreTube': {
        'url': 'https://deepgoretube.site/',
        'video_selector': '.video-item',
        'title_selector': '.video-title',
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
        'video_selector': '.video',
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
        'video_selector': '.video-item',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://alivegore.com'
    },
    'WatchPeopleDie': {
        'url': 'https://watchpeopledie.tv/',
        'video_selector': '.video',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://watchpeopledie.tv'
    },
    'E-Fukt': {
        'url': 'https://efukt.com/',
        'video_selector': '.video-item',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://efukt.com'
    },
    'Kaotic': {
        'url': 'https://kaotic.com/',
        'video_selector': '.video',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://kaotic.com'
    }
}

class VideoScraperBot:
    def __init__(self, bot_token, chat_id, db_path='videos_database.json'):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.db_path = db_path
        self.driver = None
        self.database = {}
        self.load_database()
        
    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # For GitHub Actions
        if os.getenv('GITHUB_ACTIONS') == 'true':
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def load_database(self):
        """Load existing video database from JSON file"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    self.database = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading database: {e}")
                self.database = {'videos': {}}
        else:
            self.database = {'videos': {}}
    
    def save_database(self):
        """Save video database to JSON file"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.database, f, indent=2)
        except IOError as e:
            print(f"Error saving database: {e}")
    
    def is_video_sent(self, video_url):
        """Check if video was already sent"""
        return video_url in self.database['videos']
    
    def add_video_to_db(self, site, title, url):
        """Add video to database"""
        self.database['videos'][url] = {
            'site': site,
            'title': title,
            'url': url,
            'added_at': datetime.now().isoformat(),
            'sent_at': None,
            'telegram_sent': False
        }
    
    def scrape_site(self, site_name, config):
        """Scrape a single site for videos"""
        videos = []
        try:
            print(f"Scraping {site_name}...")
            self.driver.get(config['url'])
            time.sleep(3)  # Wait for page to load
            
            # Find video elements
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, config['video_selector'])
            
            count = 0
            for video in video_elements[:10]:  # Limit to 10 videos per site
                try:
                    title_elem = video.find_element(By.CSS_SELECTOR, config['title_selector'])
                    title = title_elem.text.strip()
                    
                    link_elem = video.find_element(By.CSS_SELECTOR, config['link_selector'])
                    href = link_elem.get_attribute('href')
                    
                    if href and title:
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
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"Error processing video in {site_name}: {e}")
                    continue
            
            print(f"Found {count} new videos from {site_name}")
            return videos
            
        except Exception as e:
            print(f"Error scraping {site_name}: {e}")
            return []
    
    def send_telegram_message(self, site, title, url):
        """Send message to Telegram chat"""
        try:
            bot = Bot(token=self.bot_token)
            message = (
                f"🔥 Naya Video Aaya Hai!\n"
                f"🌐 Source: {site}\n"
                f"📌 Title: {title}\n"
                f"🔗 Watch Now: {url}"
            )
            bot.send_message(chat_id=self.chat_id, text=message)
            print(f"Sent Telegram message for: {title}")
            return True
        except TelegramError as e:
            print(f"Telegram error: {e}")
            return False
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    def run(self):
        """Main execution method"""
        print("Starting video scraper bot...")
        
        # Setup driver
        self.setup_driver()
        
        # Initialize bot
        try:
            bot = Bot(token=self.bot_token)
            bot.get_me()
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
                success = self.send_telegram_message(
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
        
        print(f"\nCompleted! Total new videos found: {len(all_videos)}")
        print(f"Videos sent to Telegram: {sent_count}")
        
        # Cleanup
        if self.driver:
            self.driver.quit()

if __name__ == '__main__':
    # Get credentials from environment variables
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7911359291:AAFIFlS55_aLnXp00zfukZQjzGhhh0kUY8I')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5412212545')
    
    bot = VideoScraperBot(BOT_TOKEN, CHAT_ID)
    bot.run()
