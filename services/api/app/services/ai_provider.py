from __future__ import annotations

import json
import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings

GROUNDED_SYSTEM_PROMPT = """You are the PGCB Institutional Assistant.

You answer questions using only:
1. Approved PGCB knowledge documents
2. Published PGCB portal content
3. Authorized member-specific tools
4. Current application data available to the authenticated user

Never invent:
- rules
- membership fees
- eligibility criteria
- official dates
- circular numbers
- employee information
- payment information
- committee decisions
- legal requirements

If authoritative information is unavailable, explicitly say so."""


class AIProvider(ABC):
    """Abstract model provider layer for the PGCB Institutional Assistant."""

    @abstractmethod
    async def generate(
        self,
        *,
        question: str,
        context: str,
        language: str = 'bn',
        history: list[dict[str, str]] | None = None,
        system_prompt: str = GROUNDED_SYSTEM_PROMPT,
    ) -> str | None:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> None:
        self.api_key = (
            api_key
            or os.getenv('AI_API_KEY')
            or os.getenv('OPENAI_API_KEY')
            or settings.ai_api_key
            or ''
        ).strip()
        self.model = (
            model
            or os.getenv('AI_MODEL')
            or os.getenv('OPENAI_MODEL')
            or settings.ai_model
            or 'gpt-4o-mini'
        ).strip()
        self.max_tokens = int(max_tokens or os.getenv('AI_MAX_TOKENS') or settings.ai_max_tokens or 600)
        self.temperature = float(
            temperature if temperature is not None else (os.getenv('AI_TEMPERATURE') or settings.ai_temperature or 0.2)
        )

    async def generate(
        self,
        *,
        question: str,
        context: str,
        language: str = 'bn',
        history: list[dict[str, str]] | None = None,
        system_prompt: str = GROUNDED_SYSTEM_PROMPT,
    ) -> str | None:
        if not self.api_key or os.getenv('AI_USE_OPENAI_LLM', 'true').lower() == 'false':
            return None

        lang_instruction = (
            'Respond in clear, institutional Bangla (বাংলা) as primary language.'
            if language == 'bn'
            else 'Respond in clear, institutional English.'
        )
        messages: list[dict[str, str]] = [
            {'role': 'system', 'content': f'{system_prompt}\n\n{lang_instruction}'},
        ]
        if history:
            for turn in history[-4:]:
                role = turn.get('role', 'user')
                content = turn.get('content', '')
                if role in ('user', 'assistant') and content:
                    messages.append({'role': role, 'content': content[:800]})

        messages.append(
            {
                'role': 'user',
                'content': f'Authoritative Context:\n{context}\n\nUser Question: {question}',
            }
        )

        try:
            req = urllib.request.Request(
                'https://api.openai.com/v1/chat/completions',
                data=json.dumps(
                    {
                        'model': self.model,
                        'temperature': self.temperature,
                        'max_tokens': self.max_tokens,
                        'messages': messages,
                    }
                ).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                llm_data: dict[str, Any] = json.loads(resp.read().decode('utf-8'))
            choices = llm_data.get('choices') or []
            if choices and choices[0].get('message', {}).get('content'):
                return str(choices[0]['message']['content']).strip()
        except Exception:
            return None
        return None


class LocalProvider(AIProvider):
    def __init__(self, endpoint_url: str | None = None, model: str | None = None) -> None:
        self.endpoint_url = (
            endpoint_url or os.getenv('AI_LOCAL_URL') or settings.ai_local_url or ''
        ).strip()
        self.model = (model or os.getenv('AI_MODEL') or settings.ai_model or 'local-llm').strip()

    async def generate(
        self,
        *,
        question: str,
        context: str,
        language: str = 'bn',
        history: list[dict[str, str]] | None = None,
        system_prompt: str = GROUNDED_SYSTEM_PROMPT,
    ) -> str | None:
        if not self.endpoint_url:
            return None
        try:
            req = urllib.request.Request(
                self.endpoint_url,
                data=json.dumps(
                    {
                        'model': self.model,
                        'temperature': 0.2,
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': f'Context:\n{context}\n\nQuestion: {question}'},
                        ],
                    }
                ).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            choices = data.get('choices') or []
            if choices and choices[0].get('message', {}).get('content'):
                return str(choices[0]['message']['content']).strip()
        except Exception:
            return None
        return None


class MockProvider(AIProvider):
    """Deterministic grounded response provider for offline/test environments."""

    async def generate(
        self,
        *,
        question: str,
        context: str,
        language: str = 'bn',
        history: list[dict[str, str]] | None = None,
        system_prompt: str = GROUNDED_SYSTEM_PROMPT,
    ) -> str | None:
        if not context.strip():
            return None
        first_block = context.strip().split('\n\n')[0]
        return first_block


def get_ai_provider() -> AIProvider:
    provider_name = (os.getenv('AI_PROVIDER') or settings.ai_provider or 'openai').strip().lower()
    if provider_name == 'local':
        return LocalProvider()
    if provider_name == 'mock':
        return MockProvider()
    return OpenAIProvider()
