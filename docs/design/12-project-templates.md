# Project Templates

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [09-configuration](09-configuration.md), [03-agent-system](03-agent-system.md)

---

## Overview

Pre-configured templates for common project types. Templates provide sensible defaults for agents, build commands, and configuration to accelerate project setup.

---

## Goals

- [ ] Provide ready-to-use configurations for common project types
- [ ] Include specialized agents per technology stack
- [ ] Generate appropriate CLAUDE.md context files
- [ ] Support template customization and extension
- [ ] Enable community template sharing

---

## Non-Goals

- Code scaffolding (templates configure orchestrator, not project code)
- IDE integration
- Language-specific tooling installation

---

## Design

### Template Structure

```
templates/
├── unreal-engine/
│   ├── template.yaml           # Main template definition
│   ├── agents/
│   │   ├── cpp-dev.yaml        # C++ developer agent
│   │   ├── blueprint-dev.yaml  # Blueprint specialist
│   │   ├── ue-builder.yaml     # UE build agent
│   │   └── ue-tester.yaml      # UE test agent
│   ├── claude.md.template      # CLAUDE.md template
│   └── README.md               # Template documentation
├── web-fullstack/
│   ├── template.yaml
│   ├── agents/
│   │   ├── frontend-dev.yaml
│   │   ├── backend-dev.yaml
│   │   ├── api-dev.yaml
│   │   └── db-dev.yaml
│   └── claude.md.template
├── python-package/
│   └── ...
├── rust-project/
│   └── ...
├── unity-game/
│   └── ...
└── mobile-app/
    └── ...
```

### Template Definition

#### `template.yaml`
```yaml
name: unreal-engine
display_name: Unreal Engine 5
description: Configuration for Unreal Engine 5 game projects
version: 1.0.0
author: Agent Orchestrator Team
tags:
  - game-development
  - cpp
  - unreal

# Setup wizard prompts
setup:
  prompts:
    - key: project_name
      question: What is your project name?
      type: text
      required: true

    - key: engine_version
      question: Which Unreal Engine version?
      type: select
      options:
        - label: "5.5 (Latest)"
          value: "5.5"
        - label: "5.4"
          value: "5.4"
        - label: "5.3"
          value: "5.3"
      default: "5.5"

    - key: project_path
      question: Where is your .uproject file?
      type: path
      required: true
      validate: "*.uproject"

    - key: use_source_control
      question: Use Git for source control?
      type: boolean
      default: true

# Default configuration
defaults:
  build:
    command: |
      "${ENGINE_PATH}/Build/BatchFiles/RunUAT.bat" BuildCookRun \
        -project="${PROJECT_PATH}" \
        -platform=Win64 \
        -configuration=Development
    timeout: 900

  test:
    command: |
      "${ENGINE_PATH}/Binaries/Win64/UnrealEditor-Cmd.exe" \
        "${PROJECT_PATH}" \
        -ExecCmds="Automation RunTests Project" \
        -unattended -nopause -testexit="Automation Test Queue Empty"
    timeout: 600

  paths:
    source:
      - Source/
      - Plugins/
    content:
      - Content/
    exclude:
      - "**/Intermediate/**"
      - "**/Binaries/**"
      - "**/Saved/**"
      - "**/DerivedDataCache/**"

# Agents to include
agents:
  - cpp-dev
  - blueprint-dev
  - ue-builder
  - ue-tester

# Pipeline defaults
pipeline:
  ideas:
    auto_refine: true
    agents:
      - clarifier
      - researcher
      - estimator
  development:
    require_build: true
    require_tests: true
    agents:
      routing:
        cpp: cpp-dev
        blueprint: blueprint-dev
        default: cpp-dev

# Variables for substitution
variables:
  ENGINE_PATH: "C:/Program Files/Epic Games/UE_${engine_version}"
  PROJECT_PATH: "${project_path}"
```

### Included Templates

#### 1. Unreal Engine 5
```yaml
name: unreal-engine
agents:
  - cpp-dev          # C++ gameplay/systems
  - blueprint-dev    # Blueprint visual scripting
  - ue-builder       # Build automation
  - ue-tester        # Automated testing
  - performance-dev  # Performance optimization
```

#### 2. Web Full-Stack
```yaml
name: web-fullstack
agents:
  - frontend-dev     # React/Vue/Svelte
  - backend-dev      # Node/Python/Go API
  - db-dev           # Database schemas/queries
  - devops-dev       # Docker/CI/CD
  - web-tester       # Jest/Playwright testing
```

#### 3. Python Package
```yaml
name: python-package
agents:
  - python-dev       # Python development
  - docs-dev         # Sphinx/MkDocs documentation
  - python-tester    # pytest testing
  - package-builder  # Build/publish
```

#### 4. Unity Game
```yaml
name: unity-game
agents:
  - csharp-dev       # C# gameplay
  - unity-editor     # Editor scripts
  - unity-builder    # Build pipeline
  - unity-tester     # Play mode tests
```

#### 5. Mobile App (React Native)
```yaml
name: mobile-app
agents:
  - rn-dev           # React Native components
  - native-ios       # iOS-specific code
  - native-android   # Android-specific code
  - mobile-tester    # Detox/Appium testing
```

#### 6. Rust Project
```yaml
name: rust-project
agents:
  - rust-dev         # Rust development
  - rust-tester      # cargo test
  - rust-docs        # rustdoc
```

### Agent Definitions

#### `agents/cpp-dev.yaml` (Unreal Engine)
```yaml
name: cpp-dev
description: Develops C++ gameplay code and systems for Unreal Engine
type: development
model: opus

tools:
  - Read
  - Edit
  - Write
  - Grep
  - Glob

allowed_paths:
  - "Source/**/*.cpp"
  - "Source/**/*.h"
  - "Plugins/**/*.cpp"
  - "Plugins/**/*.h"

blocked_paths:
  - "Source/ThirdParty/**"
  - "**/Intermediate/**"

system_prompt: |
  You are a senior Unreal Engine C++ developer.

  ## Coding Standards
  - Follow Unreal coding conventions (Epic style guide)
  - Use UPROPERTY, UFUNCTION, UCLASS macros appropriately
  - Prefix classes: A (Actor), U (Object/Component), F (Struct), E (Enum)
  - Use TArray, TMap, TSet for containers
  - Prefer smart pointers (TSharedPtr, TWeakPtr)

  ## Architecture
  - Inherit from appropriate base classes
  - Use interfaces (IInterface) for cross-cutting concerns
  - Implement Tick sparingly, prefer timers and events
  - Use subsystems for singleton-like functionality

  ## Performance
  - Cache expensive calculations
  - Use FORCEINLINE for small, hot functions
  - Profile before optimizing

  Do NOT run builds or tests - support agents handle those.

memory_scope: project
max_turns: 25
```

#### `agents/blueprint-dev.yaml` (Unreal Engine)
```yaml
name: blueprint-dev
description: Analyzes and suggests Blueprint architecture improvements
type: development
model: sonnet

tools:
  - Read
  - Grep
  - Glob

# Blueprints are binary, so this agent provides guidance
# rather than direct edits

system_prompt: |
  You are an Unreal Engine Blueprint specialist.

  Since Blueprints are binary assets, you provide:
  1. Architecture recommendations
  2. Node suggestions and patterns
  3. Performance optimization tips
  4. C++ exposure suggestions

  When reviewing Blueprint-related code:
  - Check UFUNCTION(BlueprintCallable) exposure
  - Verify UPROPERTY(EditAnywhere, BlueprintReadWrite) settings
  - Suggest Blueprint interfaces for flexibility

  Output clear, actionable instructions for manual Blueprint work.

memory_scope: project
max_turns: 10
```

### CLAUDE.md Template

#### `claude.md.template`
```markdown
# ${project_name}

## Project Overview
Unreal Engine ${engine_version} project.

## Build Commands
```bash
# Development build
${build_command}

# Run tests
${test_command}

# Open in editor
"${ENGINE_PATH}/Engine/Binaries/Win64/UnrealEditor.exe" "${PROJECT_PATH}"
```

## Code Standards
- Follow Unreal coding conventions
- Prefix: A (Actors), U (Components), F (Structs), E (Enums)
- Use UPROPERTY/UFUNCTION macros for editor/Blueprint exposure
- Keep Tick functions lightweight

## Project Structure
```
Source/
├── ${project_name}/          # Main game module
│   ├── Public/               # Headers
│   └── Private/              # Implementation
Plugins/                      # Custom plugins
Content/                      # Assets (Blueprints, Materials, etc.)
```

## Common Gotchas
- Always mark UPROPERTY to prevent garbage collection
- Use Soft References for optional assets
- Test multiplayer changes on dedicated server
- Blueprint changes require editor restart to reflect in C++
```

### Template CLI

```bash
# List available templates
agent-orchestrator templates list

# Show template details
agent-orchestrator templates info unreal-engine

# Initialize project from template
agent-orchestrator init --template unreal-engine

# Initialize with answers file (for automation)
agent-orchestrator init --template unreal-engine --answers answers.yaml
```

### Template Selection UI

```
┌─────────────────────────────────────────────────────────────────┐
│ Create New Project                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Choose a template:                                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🎮 Unreal Engine 5                           [Select]   │   │
│  │    Game development with C++ and Blueprints              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🌐 Web Full-Stack                            [Select]   │   │
│  │    Frontend + Backend + Database                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🐍 Python Package                            [Select]   │   │
│  │    Library with tests and documentation                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🎯 Unity Game                                [Select]   │   │
│  │    C# game development                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📱 Mobile App                                [Select]   │   │
│  │    React Native cross-platform                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ⚙️ Custom                                     [Select]   │   │
│  │    Start with minimal configuration                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                                              [Cancel] [Next →] │
└─────────────────────────────────────────────────────────────────┘
```

### Setup Wizard

```
┌─────────────────────────────────────────────────────────────────┐
│ Setup: Unreal Engine 5                              Step 1 of 3 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ What is your project name?                                      │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ My ARPG Game                                            │    │
│ └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│ Which Unreal Engine version?                                    │
│ ○ 5.5 (Latest)                                                  │
│ ● 5.4                                                           │
│ ○ 5.3                                                           │
│                                                                 │
│ Where is your .uproject file?                                   │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ C:/Projects/MyARPG/MyARPG.uproject                      │    │
│ └─────────────────────────────────────────────────────────┘    │
│ [Browse...]                                                     │
│                                                                 │
│                                        [← Back] [Next →]        │
└─────────────────────────────────────────────────────────────────┘
```

### Custom Template Creation

```bash
# Create template from existing project
agent-orchestrator templates create my-template --from-project ./my-project

# Export template for sharing
agent-orchestrator templates export my-template --output my-template.zip

# Import community template
agent-orchestrator templates import ./downloaded-template.zip
```

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Template marketplace? | Community sharing | TBD - defer to v2 |
| Template versioning? | Update templates over time | TBD - semver in template.yaml |
| Template inheritance? | Extend base templates | TBD - could enable stacking |

---

## Dependencies

- **Depends on**: 09-configuration, 03-agent-system
- **Depended by**: None (end-user feature)

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
