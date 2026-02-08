# DevopsMate Universal Agent - Architecture Diagram

**Last Updated:** 2024-01-XX  
**Status:** ✅ Fully Implemented - 4-Mode System with GitHub Integration + Advanced AI (RAG & Multi-Agent)

---

## 🧠 4-Mode Operating System

The DevopsMate Agent is a **mode-based intelligent agent** that operates in one of four modes based on user intent and risk level. All four modes are **fully implemented** and production-ready:

| Mode        | Purpose                             | Risk Level  | Requires Approval | LLM Powered |
| ----------- | ----------------------------------- | ----------- | ----------------- | ----------- |
| **ASK**     | Read-only intelligence & answers    | 🟢 Safe     | No                | ✅ Yes      |
| **PLAN**    | Change simulation & recommendations | 🟡 Medium   | No                | ✅ Yes      |
| **DEBUG**   | Deep inspection & diagnostics       | 🟠 Elevated | No                | ✅ Yes      |
| **EXECUTE** | Makes real changes                  | 🔴 High     | Yes               | ✅ Yes      |

### Mode Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEVOPSMATE INTELLIGENT AGENT                             │
│                      (4-Mode Operating System)                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            AGENT SERVICE                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Query Router                                       │  │
│  │  • Intent Detection                                                   │  │
│  │  • Mode Selection                                                    │  │
│  │  • Permission Check                                                  │  │
│  │  • Context Management                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼               ▼
        ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
        │   ASK MODE    │  │  PLAN MODE    │  │  DEBUG MODE   │  │ EXECUTE MODE  │
        │  (Read-Only)  │  │ (Simulation)  │  │ (Diagnostics) │  │  (Actions)    │
        │               │  │               │  │               │  │               │
        │ • 17 Handlers │  │ • LLM Plans   │  │ • LLM Analysis│  │ • LLM Parsing │
        │ • LLM Queries │  │ • Risk Assess │  │ • Root Cause  │  │ • Approval    │
        │ • Cloud Knowl │  │ • Constraints  │  │ • Deep Inspect│  │ • Execution   │
        │ • GitHub Read │  │ • Cost Est.   │  │ • Trace Anal. │  │ • GitHub PRs  │
        └───────┬───────┘  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
                │                  │                  │                  │
                └──────────────────┴──────────────────┴──────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      LLM Service              │
                    │  (Ollama - local, free)       │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   ADVANCED AI CAPABILITIES     │
                    │  ┌─────────────────────────┐  │
                    │  │   RAG Service            │  │
                    │  │  • Vector Search         │  │
                    │  │  • Context Retrieval     │  │
                    │  │  • Knowledge Base        │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │   Multi-Agent System    │  │
                    │  │  • Specialized Agents   │  │
                    │  │  • Collaboration Modes  │  │
                    │  │  • Result Synthesis     │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │   Vector Database       │  │
                    │  │  (Qdrant)               │  │
                    │  └─────────────────────────┘  │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
        ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
        │   Metrics     │  │     Logs      │  │   Topology    │
        │   Service     │  │   Service    │  │    Engine     │
        └───────────────┘  └───────────────┘  └───────────────┘
        ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
        │   GitHub      │  │   Source Code │  │   RUM Debug   │
        │   Service     │  │   Integration│  │   Symbols     │
        └───────────────┘  └───────────────┘  └───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Database Persistence        │
                    │  • AgentSession               │
                    │  • AgentQuery                 │
                    │  • AgentApproval              │
                    │  • AgentAction                │
                    │  • AgentLLMUsage              │
                    │  • AgentConversationMessage   │
                    │  • KnowledgeBase              │
                    │  • KnowledgeDocument          │
                    │  • KnowledgeChunk             │
                    │  • AgentSpecialization        │
                    │  • AgentCollaboration         │
                    └───────────────────────────────┘
```

---

## Agent Architecture Overview (Data Collection)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEVOPSMATE UNIVERSAL AGENT                               │
│                         (Running on Host/Container)                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CONFIGURATION                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  agent.yaml                                                          │  │
│  │  • Endpoint: https://api.devopsmate.com/api/v1/ingest                │  │
│  │  • API Key: dm_****                                                  │  │
│  │  • Collection intervals, paths, filters                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DISCOVERY LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │   Process    │  │  Container   │  │   Network    │                     │
│  │  Discovery   │  │  Discovery   │  │  Discovery   │                     │
│  │              │  │              │  │              │                     │
│  │ • psutil     │  │ • Docker API │  │ • netstat    │                     │
│  │ • /proc      │  │ • K8s API    │  │ • ss         │                     │
│  │ • systemd    │  │ • containerd │  │ • iptables   │                     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                     │
│         └──────────────────┴──────────────────┘                            │
│                              │                                               │
│                              ▼                                               │
│                    Topology Data (Services, Dependencies)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            COLLECTION LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │    Host      │  │  Container   │  │     Log      │  │   Network    │   │
│  │  Metrics     │  │   Metrics    │  │  Collector   │  │  Collector   │   │
│  │  Collector   │  │  Collector   │  │              │  │              │   │
│  │              │  │              │  │              │  │              │   │
│  │ • CPU        │  │ • CPU        │  │ • File tail  │  │ • Flows      │   │
│  │ • Memory     │  │ • Memory     │  │ • Journald   │  │ • Packets    │   │
│  │ • Disk I/O   │  │ • Disk I/O   │  │ • Syslog     │  │ • Bandwidth  │   │
│  │ • Network    │  │ • Network    │  │ • JSON logs  │  │ • Latency    │   │
│  │ • Processes  │  │ • Pods       │  │ • Patterns   │  │ • Errors     │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         └──────────────────┴──────────────────┴──────────────────┘          │
│                              │                                               │
│                              ▼                                               │
│                    Metrics, Logs, Traces (Raw Data)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUTO-INSTRUMENTATION LAYER                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Auto-Instrumentor                                  │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │  Python  │  │  Node.js │  │   Java   │  │   .NET   │            │  │
│  │  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │            │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │  │
│  │                                                                       │  │
│  │  • Bytecode injection                                                │  │
│  │  • Library wrapping                                                  │  │
│  │  • Trace context propagation                                         │  │
│  │  • Automatic span creation                                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                               │
│                              ▼                                               │
│                    Distributed Traces (Spans)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BUFFERING LAYER                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Data Buffer                                   │  │
│  │                                                                       │  │
│  │  • In-memory queue (survives network issues)                          │  │
│  │  • Compression (gzip, zstd)                                           │  │
│  │  • Batching (max_batch_size: 1000)                                   │  │
│  │  • Persistence (disk backup)                                          │  │
│  │  • Size limit: 10,000 items                                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXPORT LAYER                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Data Exporter                                 │  │
│  │                                                                       │  │
│  │  • HTTP/HTTPS transport                                               │  │
│  │  • OTLP (OpenTelemetry Protocol)                                     │  │
│  │  • Retry logic (exponential backoff)                                 │  │
│  │  • Authentication (API Key)                                          │  │
│  │  • Compression (gzip)                                                 │  │
│  │  • Rate limiting                                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   DevopsMate Platform API     │
                    │   https://api.devopsmate.com  │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐
            │Victoria   │  │ClickHouse │  │PostgreSQL │
            │Metrics    │  │(Logs/     │  │(Metadata) │
            │(Metrics)  │  │Traces)    │  │           │
            └───────────┘  └───────────┘  └───────────┘
```

---

## 🔌 API Endpoints

The agent is accessible via REST API:

### List Available Modes
```http
GET /api/v1/agent/modes
```

### Query Agent (Auto-detect mode)
```http
POST /api/v1/agent/query
Content-Type: application/json

{
  "query": "Is checkout service up?",
  "scope": "production"
}
```

### Query Specific Mode
```http
POST /api/v1/agent/query/ask
POST /api/v1/agent/query/plan
POST /api/v1/agent/query/debug
POST /api/v1/agent/query/execute
```

### Health Check
```http
GET /api/v1/agent/health
```

### Example Responses

**ASK Mode:**
```json
{
  "success": true,
  "mode": "ask",
  "query": "Is checkout service up?",
  "response": "Checkout service is up but experiencing 12% latency degradation since 14:32 UTC",
  "data": {
    "service_health": {
      "status": "up",
      "latency_p50": 50.0,
      "latency_p99": 200.0
    }
  },
  "confidence": 88.0,
  "execution_time_ms": 125.5
}
```

**PLAN Mode:**
```json
{
  "success": true,
  "mode": "plan",
  "query": "Deploy checkout service v2.0.0 to staging",
  "response": "Here's a step-by-step plan...",
  "data": {
    "plan": {
      "steps": [...],
      "prerequisites": [...],
      "risks": [...],
      "rollback": [...]
    }
  },
  "confidence": 92.0
}
```

**EXECUTE Mode (requires approval):**
```json
{
  "success": true,
  "mode": "execute",
  "query": "Deploy checkout service v2.0.0 to staging",
  "response": "Action parsed and ready for approval",
  "data": {
    "action": {
      "type": "deploy",
      "target": "checkout-service",
      "parameters": {...}
    },
    "approval_required": true,
    "approval_token": "approval_abc123"
  }
}
```

---

## Agent Deployment Scenarios

### Scenario 1: Standalone Host Agent
```
┌─────────────────────────────────────┐
│         Physical/Virtual Host       │
│                                     │
│  ┌───────────────────────────────┐ │
│  │   DevopsMate Agent            │ │
│  │   (Systemd Service)           │ │
│  └───────────────────────────────┘ │
│                                     │
│  Applications:                      │
│  • Web Server (nginx)               │
│  • App Server (Python/Node)         │
│  • Database (PostgreSQL)            │
└─────────────────────────────────────┘
```

### Scenario 2: Container Agent (Sidecar)
```
┌─────────────────────────────────────┐
│         Kubernetes Pod              │
│                                     │
│  ┌──────────────┐  ┌──────────────┐│
│  │   App        │  │   Agent      ││
│  │   Container  │  │   Sidecar    ││
│  │              │  │              ││
│  │  • Python    │  │  • Collects  ││
│  │  • Node.js   │  │    metrics   ││
│  │  • Java      │  │  • Logs      ││
│  └──────────────┘  └──────────────┘│
│                                     │
│  Shared: /var/log, /proc, network   │
└─────────────────────────────────────┘
```

### Scenario 3: DaemonSet (Kubernetes)
```
┌─────────────────────────────────────────────────────┐
│              Kubernetes Cluster                     │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐   │
│  │   Node 1     │  │   Node 2     │  │  Node 3  │   │
│  │              │  │              │  │          │   │
│  │  ┌────────┐  │  │  ┌────────┐  │  │ ┌──────┐ │   │
│  │  │ Agent  │  │  │  │ Agent  │  │  │ │Agent │ │   │
│  │  │(DS)    │  │  │  │(DS)    │  │  │ │(DS)  │ │   │
│  │  └────────┘  │  │  └────────┘  │  │ └──────┘ │   │
│  │              │  │              │  │          │   │
│  │  Pods...     │  │  Pods...     │  │ Pods...  │   │
│  └──────────────┘  └──────────────┘  └──────────┘   │
│                                                     │
│  Agent runs as DaemonSet (one per node)             │
└─────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────┐
│   Host OS   │
│  /proc, /sys│
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Discovery  │────▶│  Collector  │─────▶│   Buffer   │
│  (60s)      │      │  (15s)      │      │  (10s)      │
└─────────────┘      └─────────────┘      └──────┬──────┘
                                                  │
                                                  ▼
                                         ┌─────────────┐
                                         │   Exporter  │
                                         │  (HTTP/OTLP)│
                                         └──────┬──────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │  DevopsMate │
                                         │    API      │
                                         └─────────────┘
```

## Agent Components

### 1. Discovery Modules
- **Process Discovery**: Scans running processes, identifies services
- **Container Discovery**: Detects Docker/Kubernetes containers
- **Network Discovery**: Maps network connections and dependencies

### 2. Collectors
- **Host Metrics**: CPU, memory, disk, network from OS
- **Container Metrics**: Per-container resource usage
- **Log Collector**: File tailing, journald, syslog
- **Network Collector**: Flow analysis, packet capture

### 3. Auto-Instrumentation
- **Python**: Bytecode injection, library wrapping
- **Node.js**: Module patching, async hooks
- **Java**: Java Agent (javaagent), bytecode manipulation
- **.NET**: Profiling API, IL rewriting

### 4. Buffer & Export
- **Local Buffer**: In-memory + disk persistence
- **Compression**: Reduces bandwidth usage
- **Batching**: Efficient network usage
- **Retry Logic**: Handles network failures gracefully

## Resource Usage

```
┌─────────────────────────────────────┐
│      Agent Resource Limits           │
│                                     │
│  CPU:    ≤ 5% of host CPU           │
│  Memory: ≤ 256 MB                   │
│  Disk:   ≤ 100 MB (buffer)          │
│  Network: Configurable rate limit   │
└─────────────────────────────────────┘
```

## Security Features

- **API Key Authentication**: Secure communication
- **TLS Encryption**: End-to-end encryption
- **Data Isolation**: Per-tenant data separation
- **Minimal Permissions**: Runs with least privilege
- **No Data Storage**: Agent doesn't store sensitive data

## Installation Methods

### 1. Standalone Installation
```bash
# Download agent
curl -L https://downloads.devopsmate.com/agent/install.sh | bash

# Configure
cp agent.yaml.example agent.yaml
# Edit agent.yaml with your API key

# Start as service
sudo systemctl start devopsmate-agent
sudo systemctl enable devopsmate-agent
```

### 2. Docker Container
```bash
docker run -d \
  --name devopsmate-agent \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -e DEVOPSMATE_API_KEY=your_api_key \
  -e DEVOPSMATE_TENANT_ID=your_tenant_id \
  devopsmate/agent:latest
```

### 3. Kubernetes DaemonSet
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: devopsmate-agent
spec:
  selector:
    matchLabels:
      app: devopsmate-agent
  template:
    metadata:
      labels:
        app: devopsmate-agent
    spec:
      containers:
      - name: agent
        image: devopsmate/agent:latest
        env:
        - name: DEVOPSMATE_API_KEY
          valueFrom:
            secretKeyRef:
              name: devopsmate-secret
              key: api-key
        - name: DEVOPSMATE_TENANT_ID
          valueFrom:
            secretKeyRef:
              name: devopsmate-secret
              key: tenant-id
        volumeMounts:
        - name: docker-sock
          mountPath: /var/run/docker.sock
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
      volumes:
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
```

## 🧠 LLM Integration

The agent uses Large Language Models (LLMs) to provide intelligent, context-aware responses:

### Supported Provider
- **Ollama** (Local models, FREE, no API keys required)

### Advanced AI Capabilities
- **RAG (Retrieval-Augmented Generation)**: Context-aware responses using knowledge base
- **Vector Database**: Qdrant for semantic search and document retrieval
- **Knowledge Base**: Store incidents, best practices, code docs, runbooks
- **Multi-Agent System**: Specialized agents (metrics, logs, security, cost) with orchestration

### LLM Capabilities by Mode

#### ASK Mode ✅ Fully Implemented
- **Structured Handlers**: 17 specific DevOps query handlers with real data
  - Service health checks, metrics queries, log searches
  - Environment comparison, access verification
  - Network diagnostics, cost analysis
- **General Queries**: LLM-powered answers to any DevOps question
- **Cloud Knowledge**: AWS, Azure, GCP, Cloudflare, GitHub expertise
- **Context-Aware**: Uses your infrastructure data for accurate answers
- **GitHub Integration**: ✅ Read and analyze repository code
  - Repository code reading and analysis
  - File content retrieval
  - Code structure understanding
  - Best practices recommendations
- **RAG Integration**: ✅ Context-aware responses from knowledge base
  - Retrieves relevant context from past incidents
  - Searches best practices and documentation
  - Provides answers based on historical data
  - Reduces hallucinations with factual context

#### PLAN Mode
- **Structured Plans**: Step-by-step plans with prerequisites
- **Risk Assessment**: Identifies risks and mitigation strategies
- **Constraint Handling**: Respects your infrastructure constraints
- **Cost Estimation**: Estimates resource and cost implications

#### DEBUG Mode
- **Root Cause Analysis**: Deep analysis of issues
- **Trace Analysis**: Examines distributed traces
- **Pattern Recognition**: Identifies recurring issues
- **Recommendations**: Suggests fixes and improvements
- **RAG Integration**: ✅ Retrieves similar past incidents and solutions
  - Searches knowledge base for similar issues
  - Provides context from historical resolutions
  - Learns from past incident post-mortems

#### EXECUTE Mode ✅ Fully Implemented
- **Action Parsing**: Converts natural language to structured actions
- **Safety Checks**: Validates actions before execution
- **Approval Workflow**: Requires explicit approval for high-risk actions
- **Rollback Support**: Tracks actions for potential rollback
- **GitHub Integration**: ✅ Update repository code via pull requests
  - Create pull requests with code changes
  - Update files in repositories
  - Branch creation and management
  - Complete audit logging of all operations

### Configuration

Set environment variables to configure Ollama:
```bash
# Ollama (local, free) - Required
export OLLAMA_BASE_URL=http://localhost:11434/v1

# Model Selection (Optional - intelligent routing by default)
export OLLAMA_CODE_MODEL=qwen2.5-coder:32b  # For code/infra tasks (ASK, PLAN, EXECUTE)
export OLLAMA_ANALYTICS_MODEL=mixtral:8x7b  # For analytics tasks (DEBUG, RCA, metrics)
export OLLAMA_MODEL=qwen2.5-coder:32b  # Default model (fallback)
```

**Intelligent Model Routing:**
- **Code/Infrastructure Tasks** → `qwen2.5-coder:32b` (GitHub analysis, code generation, deployment planning)
- **Analytics Tasks** → `mixtral:8x7b` (Root cause analysis, log analysis, metrics interpretation)
- **General Queries** → Default model (fallback)

**RAG Integration:**
- All modes can use RAG for context-aware responses
- Query → Vector Search → Retrieve Context → Enhanced LLM Prompt → Response
- Knowledge bases: incidents, best practices, code docs, runbooks
- Automatic chunking and embedding of documents

---

## 💾 Database Persistence

All agent interactions are persisted in PostgreSQL:

### Tables

1. **`agent_sessions`** - Tracks user sessions
   - Session ID, mode, scope, status
   - Start/end times, metadata

2. **`agent_queries`** - History of all queries
   - Query text, response, mode
   - Success, confidence, execution time
   - Access control results

3. **`agent_approvals`** - Approval workflow for EXECUTE mode
   - Approval status, approver, expiration
   - Reason and metadata

4. **`agent_actions`** - Tracks executed actions
   - Action type, target resource, parameters
   - Status, duration, output, errors
   - Rollback support

5. **`agent_llm_usage`** - Tracks LLM API usage
   - Model used, tokens consumed, cost
   - Response time, task type
   - For analytics and optimization

6. **`agent_conversation_messages`** - Conversation history
   - Multi-turn conversation support
   - Context preservation across queries
   - Session-based message threading

7. **`knowledge_bases`** - Knowledge base collections
   - Categories: incidents, best_practices, code_docs, runbooks
   - Metadata and configuration

8. **`knowledge_documents`** - Documents in knowledge bases
   - Title, content, source, metadata
   - Embedding status and chunk count

9. **`knowledge_chunks`** - Chunked documents with embeddings
   - Vector embeddings for semantic search
   - Qdrant vector IDs
   - Chunk metadata

10. **`agent_specializations`** - Specialized agent definitions
    - Metrics agent, logs agent, security agent, cost agent
    - Capabilities and model preferences

11. **`agent_collaborations`** - Multi-agent collaboration tracking
    - Collaboration type (sequential, parallel, orchestrated)
    - Participating agents and results

### Benefits
- **Audit Trail**: Complete history of all agent interactions
- **Analytics**: Track usage patterns and effectiveness
- **Compliance**: Meet regulatory requirements
- **Debugging**: Investigate issues with full context
- **LLM Cost Tracking**: Monitor token usage and costs
- **Conversation Context**: Maintain context across multi-turn conversations

### GitHub Integration Tables
- **`github_repositories`** - Connected repositories
- **`github_tokens`** - Encrypted GitHub access tokens
- **`github_operations`** - Complete audit log of all GitHub operations

---

## Agent Status & Monitoring

The agent exposes metrics about itself:
- `devopsmate_agent_metrics_collected_total` - Total metrics collected
- `devopsmate_agent_logs_collected_total` - Total logs collected
- `devopsmate_agent_traces_collected_total` - Total traces collected
- `devopsmate_agent_buffer_size` - Current buffer size
- `devopsmate_agent_export_errors_total` - Export errors
- `devopsmate_agent_uptime_seconds` - Agent uptime
- `devopsmate_agent_queries_total` - Total queries processed
- `devopsmate_agent_queries_by_mode` - Queries by mode (ask/plan/debug/execute)
- `devopsmate_agent_llm_calls_total` - Total LLM API calls
- `devopsmate_agent_llm_latency_seconds` - LLM response latency

These metrics are sent to DevopsMate so you can monitor the agent's health!

---

## ✅ Implementation Status

### Core Features
- ✅ **4-Mode Operating System** - All modes fully implemented
- ✅ **LLM Integration** - Ollama integration complete with intelligent model routing
- ✅ **Database Persistence** - All interactions logged to PostgreSQL
- ✅ **GitHub Integration** - Repository reading (ASK) and code updates (EXECUTE)
- ✅ **API Endpoints** - Full REST API for all agent operations
- ✅ **Frontend Integration** - Complete UI for agent interactions
- ✅ **Advanced AI Capabilities** - RAG, Knowledge Base, and Multi-Agent System
  - ✅ **RAG (Retrieval-Augmented Generation)** - Context-aware AI responses
  - ✅ **Knowledge Base** - Document storage and retrieval
  - ✅ **Vector Database** - Qdrant integration for semantic search
  - ✅ **Multi-Agent Orchestration** - Specialized agents and collaboration

### ASK Mode Handlers (17 Total)
- ✅ Service health checks
- ✅ Metrics queries
- ✅ Log searches
- ✅ Environment comparison
- ✅ Access verification
- ✅ Network diagnostics
- ✅ Cost analysis
- ✅ GitHub repository analysis
- ✅ And 9 more specialized handlers

### GitHub Integration Features
- ✅ **Repository Code Reading** (ASK Mode)
  - Read file contents from GitHub
  - Analyze code structure
  - Understand deployment configurations
  - Provide best practice recommendations
- ✅ **Code Updates via Pull Requests** (EXECUTE Mode)
  - Create pull requests with code changes
  - Update Dockerfiles, configs, scripts
  - Branch management
  - Complete audit trail

### Data Collection (Universal Agent)
- 🟡 **Discovery** - Process, container, network discovery (scaffolding complete)
- 🟡 **Collectors** - Host metrics, container metrics, logs (scaffolding complete)
- 🟡 **Auto-Instrumentation** - Python library instrumentation (scaffolding complete)
- ✅ **Export** - OTLP and HTTP export fully implemented
- ✅ **Buffering** - In-memory buffer with persistence

### Advanced AI Integration
- ✅ **RAG Integration** - All modes can use RAG for context-aware responses
- ✅ **Knowledge Base** - Store and retrieve incidents, best practices, code docs
- ✅ **Multi-Agent System** - Specialized agents for different domains
- ✅ **Vector Search** - Semantic search for relevant context

### Next Steps
- 🔴 Complete collector implementations (host metrics, container discovery, log collection)
- 🔴 Complete auto-instrumentation for all frameworks
- 🔴 Network topology mapping
- 🔴 Full integration testing
- 🟡 Fine-tune embedding models on DevOps-specific data
- 🟡 Implement automatic knowledge extraction from incidents
- 🟡 Add more specialized agents (performance, compliance, etc.)
- 🟡 Implement agent learning from past interactions