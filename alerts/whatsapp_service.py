
import os
import time
import threading
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
try:
    from webdriver_manager.core.utils import ChromeType
except:
    pass

class WhatsAppService:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, headless=False):
        if WhatsAppService._instance:
            raise Exception("WhatsAppService is a singleton")
            
        self.driver = None
        self.headless = headless
        self.is_ready = False
        self.base_dir = Path(__file__).parent.parent
        self.user_data_dir = self.base_dir / "whatsapp_session"
        self.user_data_dir.mkdir(exist_ok=True)
        
        # Start browser in background thread
        self.start_thread = threading.Thread(target=self._init_browser, daemon=True)
        self.start_thread.start()
        
        WhatsAppService._instance = self

    @staticmethod
    def get_instance():
        with WhatsAppService._lock:
            if not WhatsAppService._instance:
                WhatsAppService()
            return WhatsAppService._instance

    def _init_browser(self):
        print("Initializing WhatsApp Service (Selenium)...")
        try:
            options = ChromeOptions()
            options.add_argument(f"user-data-dir={self.user_data_dir}")
            
            # Keep browser open but maybe minimized or headless
            # Headless often breaks WhatsApp Web QR scanning/auth.
            # We'll run normal mode first so user can scan QR.
            if self.headless:
                options.add_argument("--headless=new")
            
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--remote-allow-origins=*")
            
            # Suppress logging
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            print("Opening WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            
            # Wait for login (QR scan)
            print("Waiting for WhatsApp check (Please scan QR code if prompted)...")
            try:
                # Wait for element present after login (e.g., chat list pane)
                # This might take a while if user needs to scan
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]'))
                )
                self.is_ready = True
                print("✓ WhatsApp Service Ready!")
            except:
                print("⚠ WhatsApp Service checking timed out (User might need to scan QR)")
                # We stay open anyway so user can scan eventually
                
        except Exception as e:
            print(f"Failed to initialize WhatsApp driver: {e}")

    def send_message(self, phone, message):
        """Send message immediately using existing driver"""
        if not self.driver:
            print("WhatsApp driver not initialized")
            return False
            
        try:
            # Normalize phone
            phone = phone.replace(' ', '').replace('+', '')
            
            # Encode message
            import urllib.parse
            encoded_msg = urllib.parse.quote(message)
            
            url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
            
            # Navigate to send page
            # If we are already there, it catches the existing session
            self.driver.get(url)
            
            # Wait for send button or input box
            # 1. Wait for input box to be populated
            # 2. Wait for send button (sometimes it takes a moment to become clickable)
            
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for the chat to load
            # Look for the send button (SVG icon often used)
            # Or just wait for the input box to have text and press ENTER
            
            try:
                # Often hitting ENTER on the focused input works best
                # Wait for the main input "contenteditable"
                input_box = wait.until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                )
                
                # Double check the text is there (sometimes it's empty if invalid number)
                time.sleep(1) # Small buffer for paste
                
                input_box.send_keys(Keys.ENTER)
                print(f"✓ Message sent to {phone} (Selenium)")
                
                # Wait a bit for send confirmation (checkmark) or just buffer
                time.sleep(2)
                return True
                
            except Exception as e:
                # Fallback: look for Send button
                try:
                    send_btn = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Send"]'))
                    )
                    send_btn.click()
                    print(f"✓ Message sent to {phone} (Selenium Button Click)")
                    time.sleep(2)
                    return True
                except:
                    print(f"⚠ Could not click send: {e}")
                    # Could be invalid number popup
                    return False
                    
        except Exception as e:
            print(f"Error sending selenium message: {e}")
            return False
            
    def send_media(self, phone, file_path, caption=None):
        """Send a media file (video/image) using Selenium"""
        if not self.driver:
            print("WhatsApp driver not initialized")
            return False
            
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return False
            
        try:
            # Normalize phone
            phone = phone.replace(' ', '').replace('+', '')
            
            # Navigate to chat
            url = f"https://web.whatsapp.com/send?phone={phone}"
            self.driver.get(url)
            
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for chat to load
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
            
            # Click the plus/attach button
            attach_btn = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@title="Attach"]')))
            attach_btn.click()
            
            # Select the file input (it's hidden)
            # Find the input that accepts videos/images
            file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')))
            
            # Send file path to input
            file_input.send_keys(str(file_path.absolute()))
            
            # Wait for the preview/caption screen
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Send"]')))
            
            # Add caption if provided
            if caption:
                caption_box = self.driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="6"]')
                caption_box.send_keys(caption)
                time.sleep(1)
            
            # Click send
            send_btn = self.driver.find_element(By.XPATH, '//div[@aria-label="Send"]')
            send_btn.click()
            
            print(f"✓ Media alert sent to {phone} (Selenium)")
            time.sleep(3) # Wait for upload to complete
            return True
            
        except Exception as e:
            print(f"Error sending WhatsApp media: {e}")
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
