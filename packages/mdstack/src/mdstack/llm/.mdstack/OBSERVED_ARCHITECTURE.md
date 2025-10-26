# Observed Architecture

## Overview

The `llm` package provides a unified interface for interacting with Large Language Models (LLMs) to generate documentation. It abstracts LLM provider details behind a clean API, handles configuration management, and implements cost tracking and caching metrics. The package is designed to support multiple providers (currently Anthropic) and multiple documentation generation tasks (lookup, tests, architecture).

## Module Organization

### packages/mdstack/src/mdstack/llm/config.py
**Responsibility**: Configuration management for LLM clients, including provider selection, model mapping, API credentials, and generation parameters.

**Key exports**:
- `LLMConfig` - Configuration dataclass
- `load_config()` - Configuration loader with environment variable fallback
- `create_llm_client()` - Factory function for instantiating LLM clients

**Key patterns**:
- Supports both file-based configuration (`.mdstack.config.yaml`) and environment variable fallback
- Implements per-file-type model selection (lookup, tests, architecture can use different models)
- Maintains backward compatibility with single-model configuration format
- Searches up directory tree for configuration file

### packages/mdstack/src/mdstack/llm/client.py
**Responsibility**: LLM client implementations and response handling, including API communication, token tracking, cost estimation, and cache metrics.

**Key exports**:
- `LLMClient` - Abstract base class defining the client interface
- `AnthropicClient` - Concrete implementation for Anthropic API
- `LLMResponse` - Response dataclass with token and cost metrics

**Key patterns**:
- Abstract base class enables future provider implementations
- Detailed logging of API requests with system block tracking
- Cache-aware cost estimation with multipliers for cache operations
- Structured response object with comprehensive metrics

### packages/mdstack/src/mdstack/llm/__init__.py
**Responsibility**: Package initialization (currently empty, serves as namespace marker).

## Core Abstractions

### LLMConfig
**Location**: packages/mdstack/src/mdstack/llm/config.py
**Purpose**: Encapsulates all LLM configuration parameters including provider, model selection, API credentials, and generation settings.
**Type**: Frozen dataclass
**Key attributes**:
- `provider` - LLM provider identifier (currently "anthropic")
- `models` - Dictionary mapping file types (lookup, tests, architecture) to model names
- `api_key` - API authentication credential
- `max_tokens`, `temperature` - Generation parameters
- `enable_caching`, `cache_ttl` - Cache configuration

**Key method**:
- `get_model_for_file_type(file_type)` - Retrieves the appropriate model for a specific documentation type

### LLMClient (Abstract Base Class)
**Location**: packages/mdstack/src/mdstack/llm/client.py
**Purpose**: Defines the interface that all LLM client implementations must follow.
**Type**: Abstract base class
**Key methods**:
- `generate()` - Core method for text generation with support for system blocks and context tracking
- `get_model_name()` - Returns the model identifier

**Design rationale**: Abstraction enables support for multiple LLM providers without changing calling code.

### AnthropicClient
**Location**: packages/mdstack/src/mdstack/llm/client.py
**Purpose**: Concrete implementation of LLMClient for Anthropic's API, handling authentication, request formatting, response parsing, and metrics collection.
**Type**: Concrete class implementing LLMClient
**Key responsibilities**:
- API communication with Anthropic's messages endpoint
- System block management with cache control directives
- Token usage tracking (input, output, cache read, cache creation)
- Cost estimation based on model-specific pricing
- Detailed request/response logging with cache status visualization

### LLMResponse
**Location**: packages/mdstack/src/mdstack/llm/client.py
**Purpose**: Structured response object containing generated content and comprehensive metrics.
**Type**: Frozen dataclass
**Key attributes**:
- `content` - Generated text
- `tokens_used` - Total tokens (input + output)
- `input_tokens`, `output_tokens` - Breakdown of token usage
- `cache_creation_input_tokens`, `cache_read_input_tokens` - Cache metrics
- `cost_estimate` - Estimated cost in USD
- `model` - Model used for generation

## Critical Functions

### load_config()
**Location**: packages/mdstack/src/mdstack/llm/config.py
**Purpose**: Loads LLM configuration from file or environment variables with intelligent fallback behavior.
**Key behavior**:
- Searches up directory tree for `.mdstack.config.yaml`
- Falls back to environment variables if file not found
- Supports both new per-file-type model format and legacy single-model format
- Requires `ANTHROPIC_API_KEY` environment variable
- Returns fully initialized `LLMConfig` object

### create_llm_client()
**Location**: packages/mdstack/src/mdstack/llm/config.py
**Purpose**: Factory function that instantiates the appropriate LLM client based on configuration.
**Key behavior**:
- Validates provider is "anthropic" (only supported in Phase 1)
- Retrieves model for specific file type from config
- Returns initialized `AnthropicClient` instance

### AnthropicClient.generate()
**Location**: packages/mdstack/src/mdstack/llm/client.py
**Purpose**: Core method for generating text via Anthropic API with comprehensive logging and metrics.
**Key parameters**:
- `prompt` - User message text
- `max_tokens` - Generation limit
- `context` - Label for logging
- `input_files` - File list for logging context
- `system_blocks` - Optional list of system message blocks with cache control
- `verbose` - Enable debug-level logging

**Key behavior**:
- Logs detailed request structure including system block types and sizes
- Supports cache control directives via system blocks
- Tracks execution time and token usage
- Estimates cost based on model and cache metrics
- Returns structured `LLMResponse` with all metrics

### AnthropicClient._estimate_cost()
**Location**: packages/mdstack/src/mdstack/llm/client.py
**Purpose**: Calculates estimated cost based on token usage and cache operations.
**Key behavior**:
- Model-aware pricing (Haiku vs Sonnet)
- Cache write multiplier (1.25x for 5-minute TTL)
- Cache read multiplier (0.1x for cache hits)
- Returns cost in USD

## Architectural Patterns

### Configuration-Driven Architecture
The package uses a configuration object pattern where `LLMConfig` centralizes all settings. This enables:
- Easy switching between models and providers
- Environment-specific configuration (dev vs production)
- Per-file-type model selection for cost optimization

### Factory Pattern
`create_llm_client()` implements the factory pattern, abstracting client instantiation and enabling future provider support without changing calling code.

### Abstract Base Class Pattern
`LLMClient` defines a contract that all implementations must follow, enabling:
- Multiple provider implementations (Anthropic, OpenAI, etc.)
- Testability through mock implementations
- Clear interface documentation

### Structured Logging
The package implements detailed, structured logging that tracks:
- System block composition and sizes
- Token usage breakdown
- Cache hit/miss status with visual indicators
- Cost estimates
- Request timing

This enables monitoring and debugging of LLM operations without verbose output.

### Response Object Pattern
`LLMResponse` encapsulates all response data and metrics in a single object, providing:
- Type safety
- Clear contract for response structure
- Easy extension for new metrics
- Convenient access to all generation metadata

### Cache-Aware Cost Calculation
Cost estimation accounts for cache operations with different multipliers, reflecting Anthropic's pricing model where:
- Cache writes cost 1.25x normal input tokens
- Cache reads cost 0.1x normal input tokens

## Data Flow

1. **Configuration Loading**:
   - `load_config()` searches for `.mdstack.config.yaml` or uses environment variables
   - Returns `LLMConfig` with provider, models, and credentials

2. **Client Creation**:
   - `create_llm_client()` receives `LLMConfig` and file type
   - Instantiates `AnthropicClient` with appropriate model for that file type

3. **Text Generation**:
   - Caller invokes `AnthropicClient.generate()` with prompt and optional system blocks
   - Client formats request with system blocks and user message
   - Anthropic API processes request and returns response
   - Client extracts content and metrics from response

4. **Metrics Collection**:
   - Token counts extracted from API response
   - Cache metrics (read/creation tokens) extracted
   - Cost estimated based on model and cache operations
   - All metrics packaged in `LLMResponse`

5. **Logging**:
   - Request details logged at INFO level (model, block types, token counts)
   - Cache status logged with visual indicators
   - Full prompt logged at DEBUG level if verbose enabled
   - Response metrics logged with timing and cost

## Dependencies

**External**:
- `anthropic` - Anthropic API client library
- `pyyaml` - YAML configuration file parsing

**Internal**:
- Standard library: `os`, `pathlib`, `dataclasses`, `abc`, `logging`, `time`, `typing`

## Extension Points

### Adding New LLM Providers
1. Create new class inheriting from `LLMClient`
2. Implement `generate()` and `get_model_name()` methods
3. Update `create_llm_client()` to instantiate new provider based on config
4. Add provider-specific cost estimation logic

### Adding New File Types
1. Add new file type key to `models` dictionary in `LLMConfig`
2. Update configuration schema to include new file type
3. Calling code can request models for new file types via `get_model_for_file_type()`

### Customizing System Blocks
The `generate()` method accepts optional `system_blocks` parameter, allowing callers to:
- Provide custom system messages
- Add cache control directives to specific blocks
- Structure multi-part system prompts for different purposes

### Cost Estimation Customization
`_estimate_cost()` can be overridden in subclasses to:
- Implement different pricing models
- Add surcharges or discounts
- Support new model families with different pricing

## Key Concepts Explained

### System Blocks
System blocks are structured components of the system message sent to the LLM. Each block can have associated cache control directives. The logging system identifies block types:
- `uni-inst` - Universal instructions (first block)
- `scope-content` - Scope-specific content (middle blocks)
- `gen-content` - Generation-specific content (penultimate block)
- `gen-inst` - Generation instructions (last block)

### Cache Metrics
- **Cache creation tokens**: Tokens written to cache during this request (cost multiplier: 1.25x)
- **Cache read tokens**: Tokens read from cache during this request (cost multiplier: 0.1x)
- These enable tracking cache effectiveness and cost savings

### File Types
The package supports three documentation file types, each potentially using different models:
- `lookup` - Semantic search documentation
- `tests` - Test coverage documentation
- `architecture` - Architecture documentation

This enables cost optimization by using cheaper models for simpler tasks.

## Common Agent Tasks

### Switching LLM Providers
1. Create new class inheriting from `LLMClient` in `packages/mdstack/src/mdstack/llm/client.py`
2. Implement `generate()` method with provider-specific API calls
3. Update `create_llm_client()` in `packages/mdstack/src/mdstack/llm/config.py` to instantiate new provider
4. Add provider validation in `create_llm_client()`

### Changing Model Selection Strategy
1. Modify `LLMConfig.models` dictionary structure in `packages/mdstack/src/mdstack/llm/config.py`
2. Update `get_model_for_file_type()` logic to implement new selection strategy
3. Update configuration file parsing in `load_config()` to handle new format

### Adding New Generation Parameters
1. Add parameter to `LLMConfig` dataclass in `packages/mdstack/src/mdstack/llm/config.py`
2. Update `load_config()` to read from configuration file
3. Pass parameter through `create_llm_client()` to client instantiation
4. Use parameter in `AnthropicClient.generate()` when calling API

### Debugging LLM Requests
1. Enable verbose logging by setting `verbose=True` in `generate()` call
2. Check logs for system block composition and sizes
3. Review full prompt in DEBUG-level logs
4. Examine token usage and cache metrics in INFO-level logs
5. Verify cost estimation matches expected pricing

### Optimizing Costs
1. Review cache metrics in `LLMResponse` to identify cache hit rates
2. Consider using cheaper models (Haiku) for simpler file types
3. Adjust `cache_ttl` in configuration to balance cache effectiveness vs freshness
4. Monitor `cost_estimate` across multiple generations to identify patterns