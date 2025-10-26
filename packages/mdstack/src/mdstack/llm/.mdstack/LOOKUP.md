# Semantic Lookup Index

## LLM Configuration Management
**Search phrases**: configure LLM, LLM settings, model configuration, API key setup, provider configuration, load configuration, configuration file, YAML config, environment variables, model selection
**Files**: packages/mdstack/src/mdstack/llm/config.py
**Description**: Loading and managing LLM configuration from YAML files or environment variables. Supports per-file-type model selection (lookup, tests, architecture) with fallback defaults. Handles API key retrieval and provider setup.

## LLM Client Interface
**Search phrases**: LLM client, abstract client, client interface, generate text, LLM generation, model abstraction, provider abstraction
**Files**: packages/mdstack/src/mdstack/llm/client.py
**Description**: Abstract base class defining the LLM client interface with methods for text generation and model name retrieval. Enables support for multiple LLM providers.

## Anthropic API Integration
**Search phrases**: Anthropic client, Claude API, Anthropic integration, API communication, message creation, text generation from API, Claude models
**Files**: packages/mdstack/src/mdstack/llm/client.py
**Description**: Concrete implementation of LLM client for Anthropic's API. Handles message creation, response parsing, and integration with Claude models.

## Prompt Caching
**Search phrases**: cache control, prompt caching, cache hits, cache writes, cache TTL, cache status, cache metrics, cache tokens, cached input
**Files**: packages/mdstack/src/mdstack/llm/client.py
**Description**: Support for Anthropic's prompt caching feature. Tracks cache creation and read tokens, calculates cache hit rates, and displays cache status with visual indicators.

## Token Usage and Cost Estimation
**Search phrases**: token counting, token usage, cost estimation, pricing calculation, input tokens, output tokens, token metrics, cost per token, billing estimation
**Files**: packages/mdstack/src/mdstack/llm/client.py
**Description**: Calculates token usage from API responses and estimates costs based on model-specific pricing. Accounts for cache write and read multipliers in cost calculations.

## Request Logging and Monitoring
**Search phrases**: logging, request logging, verbose logging, debug output, performance metrics, response timing, API monitoring, request details, system blocks logging
**Files**: packages/mdstack/src/mdstack/llm/client.py
**Description**: Comprehensive logging of LLM requests including system blocks, user prompts, response metrics, timing, token usage, cache status, and cost estimates. Supports verbose mode for full prompt inspection.

## Model Selection by File Type
**Search phrases**: file type models, lookup model, tests model, architecture model, per-file-type configuration, model mapping, file-specific models
**Files**: packages/mdstack/src/mdstack/llm/config.py
**Description**: Configuration system that maps different documentation file types (lookup, tests, architecture) to specific LLM models, allowing optimization of model selection per use case.

## Client Factory
**Search phrases**: create client, client instantiation, client factory, provider selection, client creation
**Files**: packages/mdstack/src/mdstack/llm/config.py
**Description**: Factory function that creates appropriate LLM client instances based on configuration, handling provider validation and model selection.

## System Message Blocks
**Search phrases**: system message, system blocks, system prompt, cache control blocks, block types, universal instructions, generation instructions, scope content
**Files**: packages/mdstack/src/mdstack/llm/client.py
**Description**: Support for structured system message blocks with cache control annotations. Enables categorization of system blocks by type (universal instructions, generation instructions, scope content, etc.) for optimized caching.

## Configuration Fallback and Defaults
**Search phrases**: default configuration, fallback values, environment variable fallback, default models, configuration defaults, backward compatibility
**Files**: packages/mdstack/src/mdstack/llm/config.py
**Description**: Hierarchical configuration loading with sensible defaults. Supports both new per-file-type model configuration and legacy single-model format for backward compatibility.