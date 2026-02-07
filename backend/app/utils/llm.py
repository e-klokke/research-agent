"""LLM utility wrapper for Claude API"""
import os
import logging
from typing import Optional, List, Dict
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Wrapper for Claude API with prompt caching support"""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        use_cache: bool = True
    ) -> str:
        """
        Generate a response from Claude

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_cache: Whether to use prompt caching

        Returns:
            Generated text response
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            if system_prompt:
                if use_cache:
                    # Use prompt caching for system prompts
                    kwargs["system"] = [
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                else:
                    kwargs["system"] = system_prompt

            logger.info(f"Calling Claude API with {len(prompt)} chars")
            response = self.client.messages.create(**kwargs)

            result = response.content[0].text
            logger.info(f"Received response with {len(result)} chars")

            return result

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        format_instructions: Optional[str] = None,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate a structured response (JSON, markdown, etc.)

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            format_instructions: Instructions for output format
            max_tokens: Maximum tokens to generate

        Returns:
            Generated structured response
        """
        full_prompt = prompt
        if format_instructions:
            full_prompt = f"{prompt}\n\n{format_instructions}"

        return await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.3  # Lower temperature for structured output
        )


# Global instance
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create the global Claude client"""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
