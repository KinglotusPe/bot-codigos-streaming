"""
AI-based email parser using Google Gemini.
"""
import json
import logging
from google import genai
from typing import Dict, Optional
import config

logger = logging.getLogger(__name__)

class AIEmailParser:
    """Parses emails using the new Google GenAI SDK."""
    
    def __init__(self):
        """Initialize the AI parser."""
        self.api_key = config.GEMINI_API_KEY
        self.client = None
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("✅ Google GenAI Client configured successfully")
            except Exception as e:
                logger.error(f"❌ Failed to configure Google GenAI: {e}")
        else:
            logger.warning("⚠️ Gemini API Key not found. AI parsing will be disabled.")

    def parse_email(self, sender: str, subject: str, body: str) -> Dict[str, str]:
        """
        Parse email content using AI to extract security codes and links.
        
        Args:
            sender: Email sender
            subject: Email subject
            body: Email body text
            
        Returns:
            Dictionary with keys:
            - type: 'SECURITY_CODE', 'HOUSEHOLD_CODE', 'PASSWORD_RESET', 'EMAIL_CHANGE', 'OTHER'
            - code: Extracted code (OTP or household code)
            - link: Extracted link
            - platform: Detected platform name
        """
        if not self.client:
            return {'type': 'ERROR', 'error': 'AI not configured'}

        prompt = f"""
        Analyze the following email and extract security information.
        
        Sender: {sender}
        Subject: {subject}
        Body:
        {body[:2000]}
        
        Task:
        1. Classify the email type into one of these categories:
           - SECURITY_CODE: Standard OTP, 2FA, verification code for login.
           - HOUSEHOLD_CODE: Code for household/TV confirmation.
           - PASSWORD_RESET: Link or code to reset password.
           - EMAIL_CHANGE: Request to change the account email address.
           - OTHER: Promotional, billing, or irrelevant emails.
           
        2. Extract the following fields:
           - code: The numeric or alphanumeric code.
           - link: The verification or reset link.
           - platform: The service name (e.g., Netflix, HBO, Disney+).
           
        3. Return ONLY a JSON object with these keys: "type", "code", "link", "platform".
           If a field is not found, use null.
        """
        
        try:
            # Using gemini-2.0-flash which is fast and cost-effective
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            text_response = response.text.strip()
            
            # Clean up potential markdown formatting
            if text_response.startswith('```json'):
                text_response = text_response.replace('```json', '').replace('```', '')
            elif '```' in text_response:
                 # Extract JSON if it's buried in text
                 import re
                 match = re.search(r'\{.*\}', text_response, re.DOTALL)
                 if match:
                     text_response = match.group(0)
            
            result = json.loads(text_response)
            
            return {
                'type': result.get('type', 'OTHER'),
                'code': result.get('code') or '',
                'link': result.get('link') or '',
                'platform': result.get('platform') or 'Unknown'
            }
            
        except Exception as e:
            logger.error(f"❌ AI Parsing Error: {e}")
            return {'type': 'ERROR', 'error': str(e)}
