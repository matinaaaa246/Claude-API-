import asyncio
import logging
import os
import glob
import json
import time
from typing import List, Optional, Dict
from camoufox.async_api import AsyncCamoufox

logger = logging.getLogger(__name__)

class ResourceExhaustedError(Exception):
    pass

class SessionData:
    def __init__(self, cookie_data: Optional[Dict], session_id: int, cookie_file: Optional[str] = None):
        self.cookie_data = cookie_data
        self.cookie_file = cookie_file
        self.session_id = session_id
        self.is_exhausted = False
        self.exhausted_until = 0.0
        self.target_url = "https://claude.ai/new"

class PlaywrightManager:
    def __init__(self):
        self.sessions: List[SessionData] = []
        self._current_index = 0
        self.request_lock = asyncio.Lock()  # strictly 1 browser instance at a time to minimize RAM

    async def startup(self):
        logger.info("Starting Claude Manager with Camoufox (Anti-Detection Mode)...")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cookie_pattern = os.path.join(base_dir, "cookies", "*.json")
        cookie_files = glob.glob(cookie_pattern)

        if not cookie_files:
            logger.warning(f"No cookie files found in '{cookie_pattern}'. Running 1 unauthenticated session.")
            cookie_files = [None]

        for i, cookie_file in enumerate(cookie_files):
            storage_data = None
            if cookie_file:
                try:
                    with open(cookie_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                            if isinstance(data, list):
                                storage_data = {"cookies": data, "origins": []}
                            elif isinstance(data, dict):
                                storage_data = data
                            
                            if storage_data and "cookies" in storage_data:
                                for cookie in storage_data["cookies"]:
                                    if "sameSite" in cookie:
                                        val = str(cookie["sameSite"]).lower()
                                        if "none" in val:
                                            cookie["sameSite"] = "None"
                                        elif "lax" in val:
                                            cookie["sameSite"] = "Lax"
                                        elif "strict" in val:
                                            cookie["sameSite"] = "Strict"
                                        else:
                                            cookie["sameSite"] = "None"
                except Exception as e:
                    logger.error(f"Error reading cookie file {cookie_file}: {e}")
                    continue

            self.sessions.append(SessionData(storage_data, i + 1, cookie_file=cookie_file))
        
        logger.info(f"Loaded {len(self.sessions)} accounts into memory. Browsers will launch on-demand.")

    async def shutdown(self):
        logger.info("Manager shutdown complete.")

    def _get_next_available_session(self) -> SessionData:
        now = time.time()
        num_sessions = len(self.sessions)
        if num_sessions == 0:
            raise RuntimeError("No sessions available.")

        for _ in range(num_sessions):
            session = self.sessions[self._current_index]
            self._current_index = (self._current_index + 1) % num_sessions
            
            # If 5-hour limit has expired, recover the session
            if session.is_exhausted and now > session.exhausted_until:
                session.is_exhausted = False
                logger.info(f"Session {session.session_id} 5-hour limit reset. Returned to active pool.")
            
            if not session.is_exhausted:
                return session

        raise ResourceExhaustedError("All Claude accounts reached their message limits.")

    async def process_prompt(self, prompt: str) -> str:
        async with self.request_lock:
            session = self._get_next_available_session()
            logger.info(f"Routing request to Session {session.session_id}")
            
            browser = None
            context = None
            page = None
            try:
                # Use Camoufox to bypass Cloudflare Turnstile
                logger.info(f"Session {session.session_id}: Launching Camoufox...")
                async with AsyncCamoufox(headless=True, geoip=True) as browser:
                    context = await browser.new_context(
                        storage_state=session.cookie_data,
                        viewport={"width": 1366, "height": 768}
                    )
                    page = await context.new_page()
                    
                    # Abort media assets to save network and RAM
                    await page.route("**/*.{png,jpg,jpeg,webp,gif,svg,woff2,ttf,mp4,webm}", lambda route: route.abort())
                    
                    logger.info(f"Session {session.session_id}: Navigating to claude.ai/new...")
                    await page.goto(session.target_url, wait_until="domcontentloaded", timeout=60000)

                    # Wait for Cloudflare challenge check if present
                    for _ in range(20):
                        title = await page.title()
                        if "Just a moment" not in title and "challenge" not in page.url:
                            break
                        await asyncio.sleep(1)

                    # Check for login redirect
                    if "/login" in page.url:
                        raise RuntimeError(f"Session {session.session_id} cookie expired (redirected to /login).")

                    prompt_selector = 'div[contenteditable="true"], textarea, div.ProseMirror'
                    logger.info(f"Session {session.session_id}: Waiting for prompt box...")
                    await page.wait_for_selector(prompt_selector, timeout=45000)
                    
                    box = page.locator(prompt_selector).first
                    await box.click()
                    
                    # Fill prompt text safely
                    logger.info(f"Session {session.session_id}: Typing prompt...")
                    try:
                        await box.fill(prompt)
                    except Exception:
                        await page.evaluate('''(text) => {
                            const el = document.querySelector('div[contenteditable="true"], textarea, div.ProseMirror');
                            if (el) {
                                el.focus();
                                document.execCommand("selectAll", false, null);
                                document.execCommand("insertText", false, text);
                                el.dispatchEvent(new Event("input", { bubbles: true }));
                            }
                        }''', prompt)

                    await asyncio.sleep(0.5)

                    # Try pressing Enter or clicking the Send button
                    send_button = page.locator('button[aria-label*="Send"], button[aria-label*="ارسال"], button:has-text("Send")').first
                    if await send_button.count() > 0 and await send_button.is_visible():
                        await send_button.click()
                    else:
                        await page.keyboard.press("Enter")

                    # Wait for assistant response container
                    response_selector = '.font-claude-message, .prose, div[data-message-author-role="assistant"]'
                    logger.info(f"Session {session.session_id}: Waiting for response stream...")
                    await page.wait_for_selector(response_selector, timeout=60000)
                    
                    elements = await page.query_selector_all(response_selector)
                    latest_response = elements[-1]
                    
                    previous_text = ""
                    same_text_count = 0
                    current_text = ""
                    
                    for _ in range(120):
                        await asyncio.sleep(1.0)
                        current_text = await latest_response.inner_text()
                        
                        if current_text and current_text == previous_text:
                            same_text_count += 1
                            if same_text_count >= 3:
                                break
                        else:
                            same_text_count = 0
                            previous_text = current_text

                    low = current_text.lower()
                    if any(phrase in low for phrase in ["message limit", "out of messages", "try again later", "reset"]):
                        session.is_exhausted = True
                        session.exhausted_until = time.time() + (5 * 60 * 60)
                        logger.warning(f"Session {session.session_id}: Hit 5-hour limit. Marked exhausted.")
                        raise ResourceExhaustedError("Claude message limit reached.")

                    # Persist refreshed cookies
                    if session.cookie_file and os.path.exists(session.cookie_file):
                        try:
                            await context.storage_state(path=session.cookie_file)
                        except Exception:
                            pass

                    logger.info(f"Session {session.session_id}: Response complete.")
                    return current_text.strip()

            except Exception as e:
                if not isinstance(e, ResourceExhaustedError):
                    logger.error(f"Session {session.session_id} error: {e}")
                raise
