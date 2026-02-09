import json
import time
import os
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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
        self.driver = None  # Will be set up with webdriver-manager
    
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
        """Setup Selenium Chrome driver using webdriver-manager"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Use webdriver-manager to automatically download and manage chromedriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
