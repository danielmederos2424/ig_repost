from instagrapi import Client as InstaClient
import requests  
import time
import logging
import os
import pickle
from pathlib import Path
import signal
import sys
import traceback

class InstagramReelsReposter:
    def __init__(self):
        self.username = "user"
        self.password = "password"
        self.target_usernames = ["account1", "account2"] # You may add more accounts
        self.custom_caption = """Add your caption here!
        
        add some #hashtags too!"""

        self.running = True
        self.last_check = {}
        self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))
        self.logger = self._setup_logging()
        self.state_file = self.base_path / 'reposter_state.pkl'
        (self.base_path / 'logs').mkdir(exist_ok=True)
        (self.base_path / 'temp_reels').mkdir(exist_ok=True)

        # Initialize instagrapi client
        self.api = InstaClient()

        # Load previous state
        self._load_state()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _setup_logging(self):
        log_dir = self.base_path / 'logs'
        log_dir.mkdir(exist_ok=True)
        logger = logging.getLogger('InstagramReposter')
        logger.setLevel(logging.INFO)

        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_dir / 'instagram_reposter.log',
            maxBytes=5*1024*1024,
            backupCount=5
        )

        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger

    def _login(self):
        try:
            self.api.login(self.username, self.password)
            self.logger.info("Successfully authenticated")
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise

    def _load_state(self):
        try:
            if self.state_file.exists():
                with open(self.state_file, 'rb') as f:
                    self.last_check = pickle.load(f)
                self.logger.info("Loaded previous state")
            else:
                self.last_check = {username: 0 for username in self.target_usernames}
        except Exception as e:
            self.logger.error(f"Failed to load state: {str(e)}")
            self.last_check = {username: 0 for username in self.target_usernames}

    def _save_state(self):
        temp_file = self.state_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'wb') as f:
                pickle.dump(self.last_check, f)
            temp_file.rename(self.state_file)
        except Exception as e:
            self.logger.error(f"Failed to save state: {str(e)}")
            if temp_file.exists():
                temp_file.unlink()

    def _handle_shutdown(self, signum, frame):
        self.logger.info("Received shutdown signal. Cleaning up...")
        self.running = False
        self._save_state()

        temp_dir = self.base_path / 'temp_reels'
        if temp_dir.exists():
            for file in temp_dir.glob('*.mp4'):
                try:
                    file.unlink()
                except Exception as e:
                    self.logger.error(f"Failed to delete temporary file {file}: {str(e)}")

        self.logger.info("Shutdown complete")
        sys.exit(0)

    def get_new_reels_from_dms(self):
        new_reels = []
        try:
            threads = self.api.direct_threads()
            for thread in threads:
                for message in thread.messages:
                    try:
                        sender_username = self.api.username_from_user_id(message.user_id)
                    except Exception as e:
                        self.logger.error(f"Failed to fetch sender's username: {str(e)}")
                        continue

                    if (message.item_type == 'clip' and
                        sender_username in self.target_usernames and
                        message.timestamp.timestamp() > self.last_check.get(sender_username, 0)):

                        video_url = getattr(message.clip, 'video_url', None)
                        if not video_url:
                            self.logger.error(f"Video URL is missing in message {message.id}. Skipping.")
                            continue

                        reel_info = {
                            'id': message.id,
                            'video_url': video_url,
                            'timestamp': message.timestamp.timestamp(),
                            'sender_username': sender_username
                        }
                        new_reels.append(reel_info)

                if new_reels:
                    self.last_check[sender_username] = max(reel['timestamp'] for reel in new_reels)

            if new_reels:
                self._save_state()
            return new_reels
        except Exception as e:
            self.logger.error(f"Failed to get reels from DMs: {str(e)}")
            return []

    def download_reel(self, reel):
        output_dir = self.base_path / 'temp_reels'
        filename = output_dir / f"{reel['sender_username']}_{int(reel['timestamp'])}.mp4"

        try:
            response = requests.get(reel['video_url'], stream=True, timeout=30)
            response.raise_for_status()

            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk and self.running:
                        f.write(chunk)

            self.logger.info(f"Downloaded reel: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to download reel {reel['id']}: {str(e)}")
            if filename.exists():
                filename.unlink()
            return None

    def upload_reel(self, video_path):
        try:
            media = self.api.video_upload(str(video_path), caption=self.custom_caption)
            self.logger.info(f"Successfully uploaded reel: {media.pk}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload reel: {str(e)}")
            return False
        finally:
            if Path(video_path).exists():
                Path(video_path).unlink()
                self.logger.info(f"Cleaned up temporary file: {video_path}")

    def process_reels_from_dms(self):
        new_reels = self.get_new_reels_from_dms()

        for reel in new_reels:
            if not self.running:
                break

            video_path = self.download_reel(reel)
            if video_path:
                if self.upload_reel(video_path):
                    self.logger.info(f"Successfully processed reel from {reel['sender_username']}")
                time.sleep(30)  # Delay between uploads

    def run(self):
        self.logger.info("Starting Instagram Reels Reposter...")
        self.logger.info(f"Monitoring DMs for accounts: {', '.join(self.target_usernames)}")

        while self.running:
            try:
                self._login()  # Login each time we start a new cycle
                self.process_reels_from_dms()
                self.logger.info("Waiting 2 minutes before next check...")
                time.sleep(120)
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                self.logger.error(traceback.format_exc())
                time.sleep(60)

if __name__ == "__main__":
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
    
    try:
        reposter = InstagramReelsReposter()
        reposter.run()
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)
