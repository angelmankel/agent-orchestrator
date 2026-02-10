# Cost Management

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [01-architecture](01-architecture.md), [02-data-models](02-data-models.md), [03-agent-system](03-agent-system.md)

---

## Overview

Token usage tracking, cost estimation, budgets, and limits for Claude API consumption. Prevents runaway costs and provides visibility into agent efficiency.

---

## Goals

- [ ] Track token usage per agent, ticket, and project
- [ ] Calculate costs based on model pricing
- [ ] Set budgets and alerts
- [ ] Enforce hard limits to prevent overruns
- [ ] Provide usage analytics and optimization insights

---

## Non-Goals

- Billing integration (use Anthropic's billing)
- Cost allocation to external teams
- Real-time pricing updates (manual configuration)

---

## Design

### Pricing Model

```yaml
# config.yaml - Update when pricing changes
pricing:
  models:
    haiku:
      input_per_million: 0.25
      output_per_million: 1.25
    sonnet:
      input_per_million: 3.00
      output_per_million: 15.00
    opus:
      input_per_million: 15.00
      output_per_million: 75.00
  last_updated: "2026-02-01"
```

### Usage Tracking

#### Per-Request Tracking
```python
# After each Claude API call
def track_usage(
    project_id: str,
    agent_id: str,
    run_id: str,
    model: str,
    tokens_input: int,
    tokens_output: int
):
    # Calculate cost
    pricing = get_pricing(model)
    cost = (
        (tokens_input / 1_000_000) * pricing.input_per_million +
        (tokens_output / 1_000_000) * pricing.output_per_million
    )

    # Store record
    db.insert("usage_tracking", {
        "project_id": project_id,
        "agent_id": agent_id,
        "run_id": run_id,
        "model": model,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "cost_usd": cost,
        "created_at": now()
    })

    # Check limits
    check_limits(project_id)
```

#### Aggregation Queries
```sql
-- Daily usage by project
SELECT
    DATE(created_at) as date,
    project_id,
    SUM(tokens_input + tokens_output) as total_tokens,
    SUM(cost_usd) as total_cost
FROM usage_tracking
WHERE created_at >= DATE('now', '-30 days')
GROUP BY DATE(created_at), project_id;

-- Usage by agent type
SELECT
    a.type,
    a.name,
    SUM(u.tokens_input + u.tokens_output) as total_tokens,
    SUM(u.cost_usd) as total_cost,
    COUNT(DISTINCT u.run_id) as run_count,
    AVG(u.tokens_input + u.tokens_output) as avg_tokens_per_run
FROM usage_tracking u
JOIN agents a ON u.agent_id = a.id
WHERE u.created_at >= DATE('now', '-30 days')
GROUP BY a.type, a.name
ORDER BY total_cost DESC;
```

### Budgets & Limits

#### Configuration
```yaml
# config.yaml
limits:
  global:
    max_tokens_per_day: 1000000
    max_cost_per_day: 50.00
    max_cost_per_month: 500.00
    max_concurrent_agents: 5

  per_project:
    default:
      max_cost_per_day: 20.00
      max_cost_per_month: 200.00

  per_agent:
    default:
      max_tokens_per_run: 100000
      max_cost_per_run: 5.00

# Project-specific overrides
projects:
  my-arpg:
    limits:
      max_cost_per_day: 30.00
      max_cost_per_month: 300.00
```

#### Limit Types

| Limit | Scope | Action on Exceed |
|-------|-------|------------------|
| `max_tokens_per_day` | Global/Project | Block new runs |
| `max_cost_per_day` | Global/Project | Block new runs |
| `max_cost_per_month` | Global/Project | Block new runs |
| `max_tokens_per_run` | Agent | Terminate run |
| `max_cost_per_run` | Agent | Terminate run |
| `max_concurrent_agents` | Global | Queue new runs |

#### Limit Enforcement
```python
def check_limits(project_id: str) -> bool:
    # Check global daily limit
    global_today = get_usage_today(project_id=None)
    if global_today.cost >= config.limits.global.max_cost_per_day:
        raise LimitExceededError("Global daily cost limit reached")

    # Check project daily limit
    project_today = get_usage_today(project_id)
    project_limit = get_project_limit(project_id, "max_cost_per_day")
    if project_today.cost >= project_limit:
        raise LimitExceededError(f"Project daily cost limit reached")

    # Check monthly limits
    global_month = get_usage_month(project_id=None)
    if global_month.cost >= config.limits.global.max_cost_per_month:
        raise LimitExceededError("Global monthly cost limit reached")

    return True
```

### Alerts

```yaml
# config.yaml
alerts:
  thresholds:
    - percent: 50
      level: info
      message: "50% of daily budget used"
    - percent: 80
      level: warning
      message: "80% of daily budget used"
    - percent: 95
      level: critical
      message: "95% of daily budget used - approaching limit"

  notifications:
    - type: in_app  # Always enabled
    - type: email
      enabled: true
      recipients:
        - admin@example.com
    - type: webhook
      enabled: false
      url: https://hooks.example.com/alerts
```

### Usage Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│ Usage & Costs                              Period: [This Month ▼]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Summary                                                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Total Cost      │ │ Total Tokens    │ │ Agent Runs      │   │
│  │                 │ │                 │ │                 │   │
│  │   $127.45       │ │   4.2M          │ │   342           │   │
│  │   ████████░░    │ │                 │ │                 │   │
│  │   64% of $200   │ │                 │ │                 │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                                 │
│  Daily Usage                                                    │
│  ─────────────────────────────────────────────────────────────  │
│  $20 │                                                          │
│      │       ██                                                 │
│  $15 │    ██ ██ ██                                              │
│      │ ██ ██ ██ ██    ██                                        │
│  $10 │ ██ ██ ██ ██ ██ ██ ██                                     │
│      │ ██ ██ ██ ██ ██ ██ ██ ██                                  │
│   $5 │ ██ ██ ██ ██ ██ ██ ██ ██ ██                               │
│      └──────────────────────────────────────────────────────    │
│        1  2  3  4  5  6  7  8  9  10 ...                        │
│                                                                 │
│  Cost by Agent                                                  │
│  ─────────────────────────────────────────────────────────────  │
│  feature-dev     ████████████████████████  $82.30  (65%)        │
│  bugfix-dev      ████████                  $25.40  (20%)        │
│  clarifier       ████                      $12.75  (10%)        │
│  builder         ██                        $4.50   (4%)         │
│  tester          █                         $2.50   (2%)         │
│                                                                 │
│  Cost by Model                                                  │
│  ─────────────────────────────────────────────────────────────  │
│  opus            ████████████████████      $95.00  (75%)        │
│  sonnet          ████████                  $30.00  (24%)        │
│  haiku           █                         $2.45   (2%)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cost Optimization Insights

```
┌─────────────────────────────────────────────────────────────────┐
│ Optimization Suggestions                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 💡 feature-dev uses opus but averages 2k tokens/run            │
│    Consider: Switch to sonnet for ~80% cost reduction           │
│    Estimated savings: $65/month                                 │
│    [Apply] [Dismiss]                                            │
│                                                                 │
│ 💡 clarifier has high retry rate (35%)                         │
│    Consider: Improve prompts to reduce failed runs              │
│    Estimated savings: $4/month                                  │
│    [View Failures] [Dismiss]                                    │
│                                                                 │
│ 💡 builder runs on every subtask completion                    │
│    Consider: Batch builds per ticket instead                    │
│    Estimated savings: $1.50/month                               │
│    [Configure] [Dismiss]                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API Endpoints

```
GET  /api/v1/usage
GET  /api/v1/usage/summary?period=month
GET  /api/v1/usage/by-agent?period=week
GET  /api/v1/usage/by-project?period=month
GET  /api/v1/usage/daily?start=2026-02-01&end=2026-02-28

GET  /api/v1/limits
PUT  /api/v1/limits
GET  /api/v1/limits/status  # Current usage vs limits

GET  /api/v1/alerts
PUT  /api/v1/alerts/config
```

---

## Data Retention

```yaml
# config.yaml
usage:
  retention:
    detailed: 90   # Days to keep per-request records
    daily: 365     # Days to keep daily aggregates
    monthly: forever  # Keep monthly summaries indefinitely

  aggregation:
    # Run daily at 2 AM
    schedule: "0 2 * * *"
```

Aggregation process:
1. Summarize detailed records into daily aggregates
2. Delete detailed records older than retention period
3. Summarize daily aggregates into monthly summaries
4. Delete daily aggregates older than retention period

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Real-time cost display? | Show cost during agent run | TBD - update on completion |
| Cost attribution for support agents? | Builder serves all projects | TBD - allocate to ticket's project |
| Pricing API? | Auto-update from Anthropic | TBD - manual for now |

---

## Dependencies

- **Depends on**: 01-architecture, 02-data-models, 03-agent-system
- **Depended by**: 08-web-ui

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
