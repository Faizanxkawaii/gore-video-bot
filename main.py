import json
import time
import os
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# Site configurations with selectors - UPDATED based on testing
SITES = {
    'DeepGoreTube': {
        'url': 'https://deepgoretube.site/',
        'video_selector': '.video',
        'title_selector': 'h2',
        'link_selector': 'a',
        'base_url': 'https://deepgoretube.site',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'GoreCenter': {
        'url': 'https://www.gorecenter.com/',
        'video_selector': '.video-card',
        'title_selector': '.video-title',
        'link_selector': 'a',
        'base_url': 'https://www.gorecenter.com',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'BestGore': {
        'url': 'https://bestgore.fun/videos/recently-added',
        'video_selector': '.video-item',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://bestgore.fun',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'CrazyShit': {
        'url': 'https://crazyshit.com/',
        'video_selector': '.thumb',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://crazyshit.com',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'GoreSee': {
        'url': 'https://goresee.com/videos/browse',
        'video_selector': '.video-item',
        'title_selector': '.video-title',
        'link_selector': 'a',
        'base_url': 'https://goresee.com',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'SeeGore': {
        'url': 'https://seegore.com/gore/',
        'video_selector': '.post',
        'title_selector': 'h2',
        'link_selector': 'a',
        'base_url': 'https://seegore.com',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'AliveGore': {
        'url': 'https://alivegore.com/',
        'video_selector': '.thumb',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://alivegore.com',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'WatchPeopleDie': {
        'url': 'https://watchpeopledie.tv/',
        'video_selector': '.video',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://watchpeopledie.tv',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'E-Fukt': {
        'url': 'https://efukt.com/',
        'video_selector': '.thumb',
        'title_selector': '.title',
        'link_selector': 'a',
        'base_url': 'https://efukt.com',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    },
    'Kaotic': {
        'url': 'https://kaotic.com/',
        'video_selector': '.video',
        'title_selector': '.video-title',
        'link_selector': 'a',
        'base_url': 'https://kaotic.com',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }
}

class VideoScraperBot:
    def __init__(self, bot_token, chat_id, db_path='videos_database.json'):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.db_path = db_path
        self.database = {}
        self.load_database()
    
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
        """Scrape a single site for videos using requests"""
        videos = []
        try:
            print(f"Scraping {site_name}...")
            resp = requests.get(config['url'], headers=config['headers'], timeout=15)
            if resp.status_code != 200:
                print(f"HTTP {resp.status_code} for {site_name}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            video_elements = soup.select(config['video_selector'])
            
            count = 0
            for video in video_elements[:10]:
                try:
                    title_elem = video.select_one(config['title_selector'])
                    if not title_elem:
                        continue
                    title = title_elem.get_text().strip()
                    
                    link_elem = video.select_one(config['link_selector'])
                    if not link_elem:
                        continue
                    href = link_elem.get('href')
                    
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
                except Exception as e:
                    print(f"Error processing video in {site_name}: {e}")
                    continue
            
            print(f"Found {count} new videos from {site_name}")
            return videos
            
        except requests.RequestException as e:
            print(f"Request error scraping {site_name}: {e}")
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
            time.sleep(1)  # Rate limiting between sites
        
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
                    time.sleep(0.5)  # Rate limiting between messages
        
        # Save database
        self.save_database()
        
        print(f"\nCompleted! Total new videos found: {len(all_videos)}")
        print(f"Videos sent to Telegram: {sent_count}")

if __name__ == '__main__':
    # Get credentials from environment variables
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7911359291:AAFIFlS55_aLnXp00zfukZQjzGhhh0kUY8I')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5412212545')
    
    bot = VideoScraperBot(BOT_TOKEN, CHAT_ID)
    asyncio.run(bot.run())
