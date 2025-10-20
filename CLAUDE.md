# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ACE (Agentic Context Engineering) is a Python framework for self-improving language models through iterative context evolution. The framework treats context as a dynamic, evolving playbook rather than static prompts, enabling LLMs to continuously improve performance through accumulation, refinement, and organization of strategies.

## Architecture

The framework follows a modular three-component architecture:

1. **Generator (Executer)**: Generates reasoning trajectories using current playbook knowledge
2. **Reflector (Analyst)**: Analyzes execution results and extracts actionable insights
3. **Curator (Integrator)**: Integrates new insights into the evolving playbook through delta updates

### Core Data Models

- **Playbook**: Organized collection of knowledge bullets with sections
- **Bullet**: Individual knowledge items with metadata, usefulness tracking, and type classification
- **Trajectory**: Complete reasoning execution with results and generated code
- **Reflection**: Analysis insights extracted from trajectory evaluation
- **DeltaUpdate**: Incremental playbook updates preserving existing knowledge

### Multi-Provider LLM Client

The framework supports multiple LLM providers through a unified interface:
- **Custom**: ModelScope Qwen3-32B (currently configured)
- **OpenAI**: GPT models with standard API
- **Anthropic**: Claude models with native API

## Development Commands

### Environment Setup

```bash
# Install dependencies
pip install -e .

# Install with development dependencies
pip install -e .[dev]
```

### Running Examples

```bash
# Main demonstration
python main.py

# Quick demo with minimal setup
python run_example.py demo

# Basic usage examples
python run_example.py basic

# Mathematical reasoning examples
python run_example.py math

# Code generation examples
python run_example.py code
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test class
python -m pytest tests/test_ace.py::TestACEFramework -v

# Run with coverage
python -m pytest tests/ --cov=ace --cov-report=html
```

### Code Quality

```bash
# Code formatting
black ace/ examples/ tests/

# Linting
flake8 ace/ examples/ tests/

# Type checking
mypy ace/ examples/ tests/
```

## Configuration

Configuration is managed through `config.yaml` with the following key sections:

### LLM Provider Setup
- **Provider Type**: Currently set to "custom" for ModelScope
- **API Configuration**: Base URL, API keys, and default models
- **Model Parameters**: Temperature, token limits, and extra body parameters per component

### Framework Parameters
- **max_reflector_rounds**: Maximum reflection iterations (default: 3)
- **max_playbook_bullets**: Playbook size limit (default: 1000)
- **similarity_threshold**: Semantic deduplication threshold (default: 0.8)
- **max_retrieved_bullets**: Context retrieval limit (default: 10)

## Key Implementation Patterns

### Async-First Design
All components use async/await patterns for concurrent LLM API calls and non-blocking execution.

### Error Handling Strategies
- Graceful fallbacks for API failures
- Configuration validation with helpful error messages
- Comprehensive exception handling in main execution flows

### Playbook Evolution Mechanism
1. **Query Processing**: Generator retrieves relevant bullets and creates trajectory
2. **Execution Feedback**: Results (success/failure, code output, errors) captured
3. **Reflection**: Reflector analyzes patterns and extracts actionable insights
4. **Delta Integration**: Curator merges insights while preserving existing knowledge
5. **Semantic Deduplication**: Embedding-based similarity prevents redundancy

### Performance Optimization
- Incremental updates prevent context collapse
- Semantic retrieval ensures relevant context selection
- Bullet usefulness tracking optimizes future retrievals
- Configurable size limits maintain memory efficiency

## Common Usage Patterns

### Single Query Processing
```python
from ace import ACE
from ace.config_loader import get_ace_config

config = get_ace_config()
ace = ACE(config)
trajectory, reflection = await ace.solve_query("your query here")
```

### Batch Training
```python
training_queries = ["query1", "query2", "query3"]
stats = await ace.offline_adaptation(training_queries, epochs=3)
```

### Performance Evaluation
```python
test_queries = ["test1", "test2"]
results = await ace.evaluate_performance(test_queries)
print(f"Success rate: {results['success_rate']:.2%}")
```

### Playbook Management
```python
# Save/load playbook state
ace.save_playbook("playbook.json")
ace.load_playbook("playbook.json")

# Monitor evolution
summary = ace.get_playbook_summary()
stats = ace.get_statistics()
```

## API Integration Notes

### ModelScope Configuration
The framework is currently configured for ModelScope's Qwen3-32B model. The thinking mode is disabled for non-streaming calls to ensure compatibility.

### Custom Provider Support
New LLM providers can be added by extending the `LLMClient` class with appropriate API handling and response parsing.

### Code Execution
The framework includes optional code execution with configurable timeouts and sandbox settings. Currently disabled for security but can be enabled in configuration.

## Research Foundation

This implementation is based on the paper "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models" (Zhang et al., 2025). Key innovations include:

- **Context Collapse Prevention**: Incremental updates avoid knowledge loss from iterative rewriting
- **Self-Improvement Loop**: Automatic learning from execution feedback without supervised labels
- **Cost Efficiency**: 86.9% reduction in adaptation latency compared to baseline methods
- **Structured Knowledge Organization**: Bullets organized by type (strategies, error patterns, API guides, etc.)

## Current Status

✅ **Operational**: Framework successfully connects to ModelScope API and processes queries
✅ **Configuration**: YAML-based configuration loading functional
✅ **Core Components**: Generator, Reflector, and Curator operational
✅ **Examples**: Basic usage examples working across multiple domains
✅ **Testing**: Comprehensive test suite covering core functionality