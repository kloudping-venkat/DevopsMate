# DevopsMate Intelligent Agent

## 4-Mode Operating System

The DevopsMate Agent is a **mode-based intelligent agent** that operates in one of four modes based on user intent and risk level.

| Mode        | Purpose                             | Risk Level  | Requires Approval |
| ----------- | ----------------------------------- | ----------- | ----------------- |
| **ASK**     | Read-only intelligence & answers    | 🟢 Safe     | No                |
| **PLAN**    | Change simulation & recommendations | 🟡 Medium   | No                |
| **DEBUG**   | Deep inspection & diagnostics       | 🟠 Elevated | No                |
| **EXECUTE** | Makes real changes                  | 🔴 High     | Yes               |

---

## Architecture

```
agent/
├── modes/
│   ├── base.py          # Base classes and enums
│   ├── ask.py           # ASK mode 
│   ├── plan.py          # PLAN mode
│   ├── debug.py         # DEBUG mode
│   └── execute.py       # EXECUTE mode
├── service.py           # Main agent service
└── README.md           # This file
```

---

## ASK Mode - Read-Only Intelligence

**Rules:**
- ❌ No mutations
- ❌ No deployments
- ❌ No infra changes
- ✅ Read-only APIs
- ✅ Cached + live data
- ✅ Agent answers like a senior SRE

### ASK Mode Capabilities (17 Examples)

1. **Environment Compare** - Compare staging vs prod
2. **List Resources by Tag** - Find resources with specific tags
3. **Environment Health Check** - Aggregate health from multiple sources
4. **Service Status** - Check if service is up and healthy
5. **Access Check** - Who can deploy to prod? (RBAC/IAM)
6. **Repo Analysis** - Best way to deploy this service?
7. **Cost Analysis** - Break-even point for changes
8. **Schema Validation** - Is this migration safe?
9. **Version Compare** - Is prod running latest build?
10. **VM Diagnostics** - Why is VM-12 slow?
11. **DNS Check** - Is api.example.com resolving correctly?
12. **Connectivity Check** - Can prod reach Redis?
13. **Traceroute** - Where is latency introduced?
14. **Routing Check** - Are requests routed correctly?
15. **GitHub Board Sync** - Deployment status vs issues
16. **Azure Board Sync** - Same as GitHub
17. **Connectivity Issues** - Why can't service A reach service B?

---

## API Usage

### Query Agent (Auto-detect mode)

```bash
POST /api/v1/agent/query
{
  "query": "Compare staging vs prod",
  "scope": "production"
}
```

### Query Agent (Specific mode)

```bash
POST /api/v1/agent/query/ask
{
  "query": "Is checkout service up?",
  "scope": "production"
}
```

### List Available Modes

```bash
GET /api/v1/agent/modes
```

---

## Access Control

Each query is evaluated against:

```
User → Role → Scope → Resource → Action
```

### Permission Format

```
{mode}:{capability}
```

Examples:
- `ask:read_infra` - Can read infrastructure in ASK mode
- `execute:deploy` - Can deploy in EXECUTE mode
- `ask:*` - Can do anything in ASK mode

### Scope Restrictions

- **ASK mode**: Can read across scopes (with proper permissions)
- **EXECUTE mode**: Restricted to current scope

---

## Example Queries

### ASK Mode Examples

```bash
# Environment comparison
POST /api/v1/agent/query
{
  "query": "Compare staging vs prod",
  "mode": "ask"
}

# Service health
POST /api/v1/agent/query
{
  "query": "Is checkout service up?",
  "mode": "ask",
  "scope": "production"
}

# Access check
POST /api/v1/agent/query
{
  "query": "Who can deploy to prod?",
  "mode": "ask"
}

# Cost analysis
POST /api/v1/agent/query
{
  "query": "This change increases memory - is it worth it?",
  "mode": "ask",
  "metadata": {
    "change_type": "memory_increase",
    "change_value": "2GB"
  }
}
```

### PLAN Mode Examples

```bash
# Simulate change
POST /api/v1/agent/query/plan
{
  "query": "What if we scale checkout service to 10 replicas?",
  "scope": "staging"
}

# Estimate cost
POST /api/v1/agent/query/plan
{
  "query": "Estimate cost of adding 5 more VMs",
  "scope": "production"
}
```

### DEBUG Mode Examples

```bash
# Diagnose issue
POST /api/v1/agent/query/debug
{
  "query": "Why is checkout service slow?",
  "scope": "production"
}

# Trace execution
POST /api/v1/agent/query/debug
{
  "query": "Trace the execution path of request ID abc123",
  "scope": "production"
}
```

### EXECUTE Mode Examples

```bash
# Deploy (requires approval)
POST /api/v1/agent/query/execute
{
  "query": "Deploy checkout service v2.0.0 to staging",
  "scope": "staging",
  "metadata": {
    "approval_token": "approval_abc123"
  }
}
```

---

## Response Format

```json
{
  "success": true,
  "mode": "ask",
  "query": "Is checkout service up?",
  "response": "Checkout service is up but experiencing 12% latency degradation...",
  "data": {
    "service_health": {
      "status": "up",
      "latency_p50": 50.0,
      "latency_p99": 200.0
    }
  },
  "confidence": 88.0,
  "execution_time_ms": 125.5,
  "warnings": [],
  "errors": [],
  "access_denied": false
}
```

---

## Implementation Status

- ✅ **ASK Mode**: 17 capabilities implemented (handlers are stubs, need integration)
- 🟡 **PLAN Mode**: Structure complete, handlers pending
- 🟡 **DEBUG Mode**: Structure complete, handlers pending
- 🟡 **EXECUTE Mode**: Structure complete, handlers pending
- ✅ **Access Control**: RBAC system implemented
- ✅ **API Endpoints**: All endpoints created
- ⚠️ **Service Integration**: Needs connection to actual services

---

## Next Steps

1. **Complete ASK Mode Handlers** - Implement actual data fetching for all 17 capabilities
2. **Integrate with Services** - Connect to topology, metrics, logs, etc.
3. **Implement PLAN Mode** - Add simulation and estimation logic
4. **Implement DEBUG Mode** - Add deep inspection capabilities
5. **Implement EXECUTE Mode** - Add deployment and change execution
6. **Add Audit Logging** - Log all agent operations
7. **Add Approval Workflow** - For EXECUTE mode operations
