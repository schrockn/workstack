import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


def _format_cache_status(cache_read_tokens: int, cache_creation_tokens: int) -> str:
    """Format cache status with color codes for terminal output."""
    # ANSI color codes
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    RESET = "\033[0m"

    if cache_read_tokens > 0 and cache_creation_tokens > 0:
        return f"{CYAN}◐ Cache HIT + WRITE{RESET}"
    if cache_read_tokens > 0:
        return f"{GREEN}● Cache HIT{RESET}"
    if cache_creation_tokens > 0:
        return f"{YELLOW}○ Cache WRITE{RESET}"
    return f"{YELLOW}✗ No cache{RESET}"


@dataclass
class LLMResponse:
    """Response from LLM generation."""

    content: str
    tokens_used: int
    input_tokens: int
    output_tokens: int
    model: str
    cost_estimate: float
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class LLMClient(ABC):
    """Abstract LLM client."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        context: str | None = None,
        input_files: list[str] | None = None,
        verbose: bool = False,
        system_blocks: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate text from prompt.

        Args:
            prompt: User prompt text
            max_tokens: Maximum tokens to generate
            context: Context label for logging
            input_files: List of input files for logging
            verbose: Enable verbose logging
            system_blocks: Optional list of system message blocks with cache_control.
                          If None, uses default system message.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name being used."""
        pass


class AnthropicClient(LLMClient):
    """Anthropic API client."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        from anthropic import Anthropic

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        context: str | None = None,
        input_files: list[str] | None = None,
        verbose: bool = False,
        system_blocks: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        from anthropic.types import TextBlock

        # Log request start with block-level detail
        context_label = f"{context}: " if context else ""

        # Track individual system blocks with type detection
        block_details = []
        if system_blocks:
            for i, block in enumerate(system_blocks):
                if isinstance(block, dict) and "text" in block:
                    block_char_count = len(block["text"])

                    # Detect block type based on position
                    if i == 0:
                        block_type = "uni-inst"
                    elif i == len(system_blocks) - 1:
                        block_type = "gen-inst"
                    elif len(system_blocks) == 4 and i == len(system_blocks) - 2:
                        block_type = "gen-content"
                    else:
                        block_type = "scope-content"

                    block_details.append(
                        {"type": block_type, "chars": block_char_count, "index": i}
                    )

        user_chars = len(prompt)

        # Log request header
        logger.info(f"    → {context_label}{self.model}")

        # Log system blocks
        if block_details:
            logger.info("      System blocks:")
            for block in block_details:
                logger.info(f"        [{block['type']}:{block['chars']}c]")

                # Show files under scope-content block
                if block["type"] == "scope-content" and input_files:
                    # input_files are already repo-relative paths or formatted paths
                    # Just use them directly instead of extracting just the filename
                    files_str = " ".join(input_files)
                    logger.info(f"          Files: {files_str}")

        # Log user message
        # Truncate prompt if too long (show first 80 chars)
        prompt_preview = prompt[:80].replace("\n", " ")
        if len(prompt) > 80:
            prompt_preview += "..."
        logger.info(f"      User message: {user_chars}c")
        logger.info(f'        Content: "{prompt_preview}"')

        # Verbose mode: print the entire prompt
        if verbose:
            logger.debug("=" * 80)
            logger.debug(f"FULL PROMPT FOR {context or 'request'}:")
            logger.debug("=" * 80)
            if system_blocks:
                logger.debug("SYSTEM BLOCKS:")
                for block in system_blocks:
                    logger.debug(block)
                logger.debug("-" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)

        # Time the API request
        start_time = time.time()

        # Use system_blocks if provided, otherwise use default system message
        if system_blocks:
            # Type cast: Our dict structure matches TextBlockParam interface
            system_param: Any = system_blocks
        else:
            system_param = "You are a technical documentation expert."

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.1,
            system=system_param,
            messages=[{"role": "user", "content": prompt}],
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Extract text from first content block
        first_block = response.content[0]
        if isinstance(first_block, TextBlock):
            content = first_block.text
        else:
            raise ValueError(f"Unexpected content block type: {type(first_block)}")

        # Extract cache metrics
        cache_creation_tokens = getattr(response.usage, "cache_creation_input_tokens", 0)
        cache_read_tokens = getattr(response.usage, "cache_read_input_tokens", 0)

        # Log cache status with token details
        cache_status = _format_cache_status(cache_read_tokens, cache_creation_tokens)
        token_details = ""
        if cache_read_tokens > 0 or cache_creation_tokens > 0:
            parts = []
            if cache_read_tokens > 0:
                parts.append(f"{cache_read_tokens:,} read")
            if cache_creation_tokens > 0:
                parts.append(f"{cache_creation_tokens:,} write")
            token_details = f" ({', '.join(parts)})"
        logger.info(f"       {cache_status}{token_details}")

        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        cost = self._estimate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
            cache_creation_tokens,
            cache_read_tokens,
        )

        # Log request completion with detailed metrics
        cache_info = ""
        if cache_creation_tokens > 0:
            cache_info = f" | cache write: {cache_creation_tokens:,} tokens"
        if cache_read_tokens > 0:
            total_input = response.usage.input_tokens + cache_read_tokens
            savings_pct = int(cache_read_tokens / total_input * 100)
            cache_info = f" | cache hit: {cache_read_tokens:,} tokens ({savings_pct}% cached)"

        logger.info(
            f"    ✓ {context_label}{self.model} | {duration_ms}ms | "
            f"{response.usage.input_tokens:,} in + {response.usage.output_tokens:,} out = "
            f"{tokens_used:,} total tokens{cache_info} | ${cost:.4f}"
        )

        return LLMResponse(
            content=content,
            tokens_used=tokens_used,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=self.model,
            cost_estimate=cost,
            cache_creation_input_tokens=cache_creation_tokens,
            cache_read_input_tokens=cache_read_tokens,
        )

    def get_model_name(self) -> str:
        return self.model

    def _estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> float:
        """Estimate cost based on Anthropic pricing."""
        # Pricing per million tokens (approximate)
        if "haiku" in self.model.lower():
            # Claude Haiku pricing
            input_cost_per_1m = 1.00
            output_cost_per_1m = 5.00
        elif "sonnet" in self.model.lower():
            # Claude Sonnet pricing
            input_cost_per_1m = 3.00
            output_cost_per_1m = 15.00
        else:
            # Default to Sonnet pricing for unknown models
            input_cost_per_1m = 3.00
            output_cost_per_1m = 15.00

        # Cache pricing multipliers
        cache_write_multiplier = 1.25  # 5-minute TTL
        cache_read_multiplier = 0.1

        cost = (
            input_tokens / 1_000_000 * input_cost_per_1m
            + output_tokens / 1_000_000 * output_cost_per_1m
            + cache_creation_tokens / 1_000_000 * input_cost_per_1m * cache_write_multiplier
            + cache_read_tokens / 1_000_000 * input_cost_per_1m * cache_read_multiplier
        )

        return cost
