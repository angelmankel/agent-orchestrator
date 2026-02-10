# Configuration System

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [01-architecture](01-architecture.md), [03-agent-system](03-agent-system.md)

---

## Overview

Configuration system for projects, agents, and global settings. Supports inheritance, overrides, and templates for quick project setup.

---

## Goals

- [ ] Define clear configuration hierarchy
- [ ] Support project templates for common setups
- [ ] Enable per-project agent customization
- [ ] Store configuration in portable formats
- [ ] Validate configuration on load

---

## Non-Goals

- Runtime configuration hot-reloading
- GUI configuration editor (use files + UI forms)
- Encrypted configuration storage

---

## Design

### Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Configuration Hierarchy                      │
└─────────────────────────────────────────────────────────────────┘

     Lowest Priority                              Highest Priority
           │                                             │
           ▼                                             ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Defaults │ -> │ Template │ -> │ Project  │ -> │  User    │
    │          │    │          │    │          │    │ Override │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Configuration Files

#### Global Configuration
`~/.agent-orchestrator/config.yaml`

```yaml
# Global defaults
defaults:
  model: sonnet
  max_tokens: 100000
  timeout_seconds: 300

# API configuration
api:
  host: localhost
  port: 8000
  cors_origins:
    - http://localhost:3000

# Claude API
claude:
  api_key: ${ANTHROPIC_API_KEY}  # Environment variable
  default_model: claude-sonnet-4-20250514

# Database
database:
  path: ~/.agent-orchestrator/data.db

# Usage limits
limits:
  max_tokens_per_day: 1000000
  max_cost_per_day: 50.00
  max_concurrent_agents: 5

# User preferences
preferences:
  theme: system  # light, dark, system
  notifications: true
  auto_approve_builds: false
```

#### Project Configuration
`<project>/.agent-orchestrator/config.yaml`

```yaml
# Project metadata
project:
  name: My ARPG Game
  description: An action RPG built with Unreal Engine 5
  type: unreal-engine  # References template

# Build configuration
build:
  command: ./Build.sh
  timeout: 600
  working_directory: .

# Test configuration
test:
  command: ./RunTests.sh
  pattern: "**/*Test.cpp"
  timeout: 300

# Source paths
paths:
  source:
    - Source/
    - Plugins/
  exclude:
    - "**/Intermediate/**"
    - "**/Binaries/**"
    - "**/.git/**"

# Agent overrides (merged with global agents)
agents:
  feature-dev:
    allowed_paths:
      - Source/ARPG/**
      - Plugins/**
    blocked_paths:
      - Source/ThirdParty/**

# Project-specific agents
custom_agents:
  - name: spawning-plugin
    description: Handles spawning system changes
    type: development
    model: sonnet
    tools: [Read, Edit, Grep, Glob]
    allowed_paths:
      - Plugins/SpawningSystem/**
    system_prompt: |
      You only modify the SpawningSystem plugin.
      Follow existing patterns in SpawnManager.h.

# Pipeline configuration
pipeline:
  ideas:
    auto_refine: true
    require_questions: true
    min_subtasks: 1
  development:
    require_build: true
    require_tests: true
    require_review: true
```

### Templates

Templates provide pre-configured setups for common project types.

#### Template Structure
```
templates/
├── unreal-engine/
│   ├── template.yaml
│   └── agents/
│       ├── blueprint-dev.yaml
│       └── cpp-dev.yaml
├── web-app/
│   ├── template.yaml
│   └── agents/
│       ├── frontend-dev.yaml
│       └── backend-dev.yaml
└── python-package/
    ├── template.yaml
    └── agents/
        └── python-dev.yaml
```

#### Template Definition
`templates/unreal-engine/template.yaml`

```yaml
name: unreal-engine
description: Unreal Engine 5 game project
version: 1.0.0

# Default configuration for UE5 projects
defaults:
  build:
    command: ./Build.sh
    timeout: 600
  test:
    command: ./RunTests.sh
    timeout: 300
  paths:
    source:
      - Source/
      - Plugins/
    exclude:
      - "**/Intermediate/**"
      - "**/Binaries/**"
      - "**/Saved/**"

# Agents included with this template
agents:
  - blueprint-dev
  - cpp-dev
  - ue-builder
  - ue-tester

# Suggested CLAUDE.md content
claude_md: |
  # Unreal Engine 5 Project

  ## Build Commands
  - Build: `./Build.sh`
  - Test: `./RunTests.sh`
  - Editor: Open .uproject in Unreal Editor

  ## Code Standards
  - Follow Unreal coding conventions
  - Prefix: A (Actors), U (Components), F (Structs)
  - Use UPROPERTY/UFUNCTION macros

# Setup prompts when initializing
setup:
  prompts:
    - key: project_name
      question: What is your project name?
      type: text
    - key: engine_version
      question: Which Unreal Engine version?
      type: select
      options: ["5.3", "5.4", "5.5"]
```

### Agent Configuration Schema

```yaml
# Full agent configuration schema
name: string                    # Required: unique identifier
description: string             # Required: when to use this agent
type: enum                      # Required: refinement|development|support|planning

# Model settings
model: enum                     # haiku|sonnet|opus (default: sonnet)
max_turns: integer              # Max API rounds (default: 20)
timeout_seconds: integer        # Max runtime (default: 300)

# Tool configuration
tools: array[string]            # Allowed tools
disallowed_tools: array[string] # Explicitly blocked

# Prompt
system_prompt: string           # Base instructions
context_files: array[string]    # Always include these files

# Path restrictions
allowed_paths: array[string]    # Glob patterns for access
blocked_paths: array[string]    # Glob patterns to block

# Memory
memory_scope: enum              # none|session|project|global

# Approval gates
require_approval: array[string] # Actions needing human OK
  # Examples: "Write(new files)", "Edit(*.h)", "Bash(*)"

# Metadata
tags: array[string]             # For filtering/organization
is_active: boolean              # Enable/disable (default: true)
```

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional overrides
AGENT_ORCH_HOST=0.0.0.0
AGENT_ORCH_PORT=8080
AGENT_ORCH_DB_PATH=/custom/path/data.db
AGENT_ORCH_LOG_LEVEL=debug
AGENT_ORCH_MAX_TOKENS=500000
```

### Configuration Merging

```python
# Pseudocode for configuration resolution
def resolve_config(project_path):
    # 1. Start with built-in defaults
    config = load_defaults()

    # 2. Apply template if specified
    if project.type:
        template = load_template(project.type)
        config = deep_merge(config, template.defaults)

    # 3. Apply project configuration
    project_config = load_yaml(f"{project_path}/.agent-orchestrator/config.yaml")
    config = deep_merge(config, project_config)

    # 4. Apply user overrides
    user_config = load_yaml("~/.agent-orchestrator/config.yaml")
    config = deep_merge(config, user_config.get("projects", {}).get(project.name, {}))

    # 5. Apply environment variables
    config = apply_env_overrides(config)

    return config
```

### Validation

```yaml
# Configuration validation rules
validation:
  project:
    name:
      required: true
      max_length: 64
    path:
      required: true
      must_exist: true

  agent:
    name:
      required: true
      pattern: "^[a-z][a-z0-9-]*$"
      max_length: 32
    type:
      required: true
      enum: [refinement, development, support, planning]
    model:
      enum: [haiku, sonnet, opus]
    tools:
      valid_values: [Read, Edit, Write, Grep, Glob, Bash, WebSearch, WebFetch]

  build:
    command:
      required: true
    timeout:
      min: 30
      max: 3600
```

---

## UI Configuration

### Project Settings Page
```
┌─────────────────────────────────────────────────────────────────┐
│ Project Settings: My ARPG                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ General                                                         │
│ ─────────────────────────────────────────────────────────────── │
│ Name:        [My ARPG________________________]                  │
│ Description: [An action RPG built with UE5___]                  │
│ Template:    [Unreal Engine ▼]                                  │
│                                                                 │
│ Build & Test                                                    │
│ ─────────────────────────────────────────────────────────────── │
│ Build Command: [./Build.sh___________________]                  │
│ Test Command:  [./RunTests.sh________________]                  │
│ Build Timeout: [600_] seconds                                   │
│                                                                 │
│ Paths                                                           │
│ ─────────────────────────────────────────────────────────────── │
│ Source Paths:                                                   │
│   [Source/          ] [×]                                       │
│   [Plugins/         ] [×]                                       │
│   [+ Add Path]                                                  │
│                                                                 │
│ Excluded Paths:                                                 │
│   [**/Intermediate/**] [×]                                      │
│   [**/Binaries/**   ] [×]                                       │
│   [+ Add Exclusion]                                             │
│                                                                 │
│                                              [Cancel] [Save]    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Config file format? | YAML vs JSON vs TOML | TBD - YAML for readability |
| Secrets management? | API keys, credentials | TBD - env vars + optional vault |
| Config versioning? | Track config changes | TBD - git for project configs |

---

## Dependencies

- **Depends on**: 01-architecture, 03-agent-system
- **Depended by**: 04-ideas-pipeline, 05-development-pipeline, 12-project-templates

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
