"""
LLM integration for Ghost Brain.
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Tuple

import google.generativeai as genai
import openai
from google.api_core.exceptions import GoogleAPIError
from google.generativeai.types import (
    BlockedPromptException,
    StopCandidateException,
)

from .config import BrainConfig


class LLMHandler:
    """Handles communication with LLM providers."""
    
    def __init__(self, config: BrainConfig):
        self.config = config
        self._setup_clients()
        
    def _setup_clients(self):
        """Initialize API clients."""
        if self.config.llm.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.config.llm.openai_api_key)
        else:
            self.openai_client = None
            
        if self.config.llm.gemini_api_key:
            genai.configure(api_key=self.config.llm.gemini_api_key)
        else:
            genai.configure(api_key="")  # Will fail gracefully if no key
            
    async def get_response(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        user_prompt: str,
        model_type: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Optional[str]:
        """Get response from LLM provider."""
        
        # Determine which model to use
        if model_type is None:
            # Auto-select based on available API keys
            if self.openai_client:
                model_type = "openai"
                model_name = model_name or self.config.llm.openai_model
            elif self.config.llm.gemini_api_key:
                model_type = "gemini"
                model_name = model_name or self.config.llm.gemini_model
            else:
                print("ERROR: No API keys configured")
                return None
                
        try:
            if model_type == "openai":
                return await self._get_openai_response(system_prompt, history, user_prompt, model_name)
            elif model_type == "gemini":
                return await self._get_gemini_response(system_prompt, history, user_prompt, model_name)
            else:
                print(f"ERROR: Unknown model type '{model_type}'")
                return None
                
        except Exception as e:
            print(f"ERROR: LLM request failed: {e}")
            return None
            
    async def _get_openai_response(
        self, 
        system_prompt: str, 
        history: List[Dict[str, Any]], 
        user_prompt: str,
        model_name: str
    ) -> Optional[str]:
        """Get response from OpenAI."""
        if not self.openai_client:
            print("ERROR: OpenAI client not configured")
            return None
            
        messages_payload = [
            {"role": "system", "content": system_prompt}
        ] + [
            {"role": "assistant" if m["role"] == "model" else "user", "content": m["content"]}
            for m in reversed(history)
        ] + [
            {"role": "user", "content": user_prompt}
        ]

        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model=model_name,
            messages=messages_payload,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
        )
        
        return response.choices[0].message.content

    async def _get_gemini_response(
        self, 
        system_prompt: str, 
        history: List[Dict[str, Any]], 
        user_prompt: str,
        model_name: str
    ) -> Optional[str]:
        """Get response from Google Gemini."""
        if not self.config.llm.gemini_api_key:
            print("ERROR: Gemini API key not configured")
            return None
            
        gemini_model = genai.GenerativeModel(
            model_name,
            system_instruction=system_prompt,
        )

        gemini_history = []
        for msg in reversed(history):
            role_for_gemini = "model" if msg["role"] == "model" else "user"
            # Merge consecutive user/model messages as required by Gemini API
            if gemini_history and gemini_history[-1]["role"] == role_for_gemini:
                gemini_history[-1]["parts"][0] += f"\n\n{msg['content']}"
            else:
                gemini_history.append({"role": role_for_gemini, "parts": [msg["content"]]})

        chat_session = gemini_model.start_chat(history=gemini_history)
        response = await chat_session.send_message_async(user_prompt)
        return response.text

    async def get_summary(self, text: str) -> Optional[str]:
        """Get summary of text using summarizer model."""
        summarizer_config = {
            "model_type": self.config.llm.summarizer_type,
            "model_name": self.config.llm.summarizer_model,
            "system_prompt": (
                "You are a helpful assistant tasked with summarizing conversation content. "
                "Provide a concise factual summary of the given text, focusing on key topics "
                "and information discussed. Do not add opinions or conversational filler."
            ),
        }
        
        return await self.get_response(
            system_prompt=summarizer_config["system_prompt"],
            history=[],
            user_prompt=text,
            model_type=summarizer_config["model_type"],
            model_name=summarizer_config["model_name"]
        )

    def parse_structured_response(self, raw_response: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse structured JSON response with fallback."""
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                response_to_user = data.get('response_to_user', '')
                reasoning = data.get('reasoning', '')
                return response_to_user, reasoning
            except json.JSONDecodeError:
                pass
                
        # Fallback: return raw response as user response, empty reasoning
        return raw_response, None

    def create_structured_prompt(self, base_prompt: str) -> str:
        """Create a prompt that encourages structured JSON responses."""
        return f"""{base_prompt}

Please respond in the following JSON format:
{{
    "response_to_user": "Your response to the user",
    "reasoning": "Your internal reasoning process"
}}

If you cannot provide a structured response, respond normally.""" 