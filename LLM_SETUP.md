# LLM Setup for DevopsMate Agent

**Last Updated:** 2024-01-XX  
**Status:** ✅ Fully Configured - Ollama Integration + Advanced AI (RAG & Multi-Agent) Complete

---

## Overview

The DevopsMate Agent uses Large Language Model (LLM) capabilities to provide intelligent DevOps assistance across all four modes (ASK, PLAN, DEBUG, EXECUTE). The agent leverages **Ollama** - a local, open-source LLM runtime that runs entirely on your infrastructure.

**Advanced AI Capabilities:**
- **RAG (Retrieval-Augmented Generation)**: Context-aware responses using knowledge base
- **Knowledge Base Management**: Store and retrieve incidents, best practices, code docs
- **Multi-Agent System**: Specialized agents (metrics, logs, security, cost) with orchestration
- **Vector Database**: Qdrant for semantic search and document retrieval

---

## What LLM We're Using

### **Ollama - Local LLM Runtime**

**Ollama** is an open-source tool that allows you to run large language models locally on your machine or server. It provides an OpenAI-compatible API, making it easy to integrate with existing LLM applications.

**Primary Models:**
- **`qwen2.5-coder:32b`** - Code and infrastructure tasks (18GB VRAM)
- **`mixtral:8x7b`** - Analytics and reasoning tasks (optimized for analysis)

**Why Ollama Specifically:**
1. **100% Local** - Runs entirely on your infrastructure
2. **Open Source** - No vendor lock-in, full control
3. **OpenAI-Compatible API** - Easy integration with existing code
4. **Multiple Model Support** - Can run different models for different tasks
5. **No API Keys** - No external dependencies or authentication
6. **Free Forever** - No usage costs, no token limits

---

## Why We're Using Ollama (vs. OpenAI, Anthropic, etc.)

### 1. **Cost Efficiency** 💰
**Problem with Cloud LLMs:**
- OpenAI GPT-4: ~$0.03-0.06 per 1K tokens (input), ~$0.06-0.12 per 1K tokens (output)
- Anthropic Claude: ~$0.008-0.015 per 1K tokens (input), ~$0.024-0.075 per 1K tokens (output)
- **For a DevOps agent making 1000 queries/day**: $30-120/day = **$900-3,600/month**
- **For enterprise with 10,000 queries/day**: **$9,000-36,000/month**

**Ollama Solution:**
- **$0 per query** - One-time hardware cost
- **No token limits** - Unlimited usage
- **No API rate limits** - Full control over throughput
- **ROI**: Hardware pays for itself in 1-3 months

### 2. **Data Privacy & Security** 🔒
**Problem with Cloud LLMs:**
- Code, infrastructure details, and sensitive data sent to external APIs
- Compliance concerns (GDPR, HIPAA, SOC 2)
- Risk of data leaks or unauthorized access
- Vendor data retention policies

**Ollama Solution:**
- **100% Private** - All data stays on your infrastructure
- **No External Calls** - Zero data leaves your network
- **Compliance Ready** - Meets strict regulatory requirements
- **Audit Trail** - Full control over data access logs

### 3. **Reliability & Uptime** ⚡
**Problem with Cloud LLMs:**
- API outages affect your agent
- Rate limiting can throttle operations
- Network latency adds delay
- Vendor lock-in risk

**Ollama Solution:**
- **No External Dependencies** - Works offline
- **Predictable Performance** - No rate limits
- **Low Latency** - Local processing (10-100ms vs 500-2000ms)
- **No Vendor Lock-in** - Open source, can switch models

### 4. **Customization & Control** 🎛️
**Problem with Cloud LLMs:**
- Limited model selection
- Can't fine-tune for DevOps tasks
- Fixed pricing and limits
- No control over model updates

**Ollama Solution:**
- **Any Model** - Run any compatible model (Llama, Mistral, Qwen, etc.)
- **Fine-tuning** - Can fine-tune models for DevOps-specific tasks
- **Version Control** - Pin specific model versions
- **Full Control** - Configure temperature, context length, etc.

### 5. **Project Philosophy Alignment** 🎯
**DevopsMate Core Values:**
- **Cost Efficiency** - Provide enterprise features at fraction of cost
- **Privacy First** - Customer data never leaves their infrastructure
- **Open Source Friendly** - Built on open standards (OpenTelemetry, etc.)
- **Vendor Independence** - No lock-in to proprietary services

**Ollama Aligns Perfectly:**
- ✅ Free and open source
- ✅ Runs on customer infrastructure
- ✅ No vendor lock-in
- ✅ Full control and transparency

---

## How Ollama Fits Our Project

### 1. **Multi-Tenant SaaS Architecture**
- Each tenant can run their own Ollama instance
- Complete data isolation (no cross-tenant data leakage)
- Tenant-specific model configurations
- Per-tenant cost tracking (hardware costs, not API costs)

### 2. **4-Mode Agent System**
- **ASK Mode**: Fast, local responses for DevOps queries
- **PLAN Mode**: Generate deployment plans without external API calls
- **DEBUG Mode**: Analyze logs and traces locally (sensitive data stays private)
- **EXECUTE Mode**: Parse actions and generate code changes locally

### 3. **Intelligent Model Routing**
- **Code Tasks** → `qwen2.5-coder:32b` (optimized for infrastructure/code)
- **Analytics Tasks** → `mixtral:8x7b` (optimized for reasoning/analysis)
- Automatic task detection and model selection
- Fallback to default model if specific model unavailable

### 4. **Cost Intelligence Integration**
- LLM usage tracked in `agent_llm_usage` table
- Token counting for analytics (cost = $0, but useful for monitoring)
- Can correlate LLM usage with cost savings from automation
- Hardware cost attribution to tenants

### 5. **GitHub Integration**
- Code analysis happens locally (no code sent to external APIs)
- Repository reading and analysis in ASK mode
- Code generation for pull requests in EXECUTE mode
- All sensitive code stays on-premises

### 6. **Advanced AI Integration (RAG & Multi-Agent)**
- **RAG (Retrieval-Augmented Generation)**: Enhances LLM responses with relevant context from knowledge base
- **Knowledge Base**: Store historical incidents, best practices, code documentation, runbooks
- **Vector Search**: Semantic search for relevant context using Qdrant
- **Multi-Agent Orchestration**: Specialized agents collaborate on complex queries
- **Context-Aware Responses**: Reduces hallucinations by providing factual context
- All knowledge base data stays local (Qdrant can run on-premises)

---

## Pros and Cons

### ✅ **PROS - Advantages of Using Ollama**

#### 1. **Cost Benefits**
- ✅ **Zero API Costs** - No per-token or per-request charges
- ✅ **Predictable Expenses** - Only hardware costs (one-time or monthly)
- ✅ **Unlimited Usage** - No token limits or rate limits
- ✅ **Scalable Economics** - Cost per query decreases with usage
- ✅ **ROI** - Pays for itself quickly at high usage

#### 2. **Privacy & Security**
- ✅ **100% Private** - All data stays on your infrastructure
- ✅ **No Data Leakage Risk** - Zero external API calls
- ✅ **Compliance Ready** - Meets GDPR, HIPAA, SOC 2 requirements
- ✅ **Audit Control** - Full control over access logs
- ✅ **Sensitive Data Safe** - Code, configs, credentials never leave your network

#### 3. **Performance**
- ✅ **Low Latency** - 10-100ms response time (vs 500-2000ms for cloud APIs)
- ✅ **No Rate Limits** - Process as many queries as hardware allows
- ✅ **Predictable Performance** - No external dependencies
- ✅ **Offline Capable** - Works without internet connection
- ✅ **Batch Processing** - Can process multiple queries in parallel

#### 4. **Control & Flexibility**
- ✅ **Model Selection** - Choose best model for each task type
- ✅ **Version Control** - Pin specific model versions
- ✅ **Fine-tuning** - Can fine-tune models for DevOps tasks
- ✅ **Configuration** - Full control over temperature, context, etc.
- ✅ **No Vendor Lock-in** - Open source, can switch anytime

#### 5. **Reliability**
- ✅ **No External Dependencies** - Not affected by cloud API outages
- ✅ **Uptime Control** - You control availability
- ✅ **No Network Issues** - Local processing eliminates network latency
- ✅ **Predictable Costs** - No surprise bills from API usage

#### 6. **Development & Testing**
- ✅ **Free Development** - No costs during development/testing
- ✅ **Easy Testing** - Test without worrying about API costs
- ✅ **Rapid Iteration** - No rate limits during development
- ✅ **Local Debugging** - Can debug LLM calls locally

---

### ❌ **CONS - Disadvantages & Limitations**

#### 1. **Hardware Requirements**
- ❌ **GPU Needed** - Requires GPU for optimal performance (8GB+ VRAM recommended)
- ❌ **CPU Mode Slow** - Can run on CPU but 10-50x slower
- ❌ **Memory Intensive** - Large models need 16-64GB RAM
- ❌ **Storage** - Models are large (7GB-40GB per model)
- ❌ **Initial Setup** - Requires hardware provisioning and setup

#### 2. **Model Quality**
- ❌ **May Lag Behind** - Local models may not be as advanced as latest GPT-4/Claude
- ❌ **Context Window** - Some models have smaller context windows (8K-32K vs 128K+)
- ❌ **Fine-tuning Required** - May need fine-tuning for specific DevOps tasks
- ❌ **Model Selection** - Need to choose and maintain multiple models

#### 3. **Operational Overhead**
- ❌ **Infrastructure Management** - Need to manage Ollama servers
- ❌ **Model Updates** - Need to manually update models
- ❌ **Monitoring** - Need to monitor GPU/CPU usage, model health
- ❌ **Scaling** - Need to scale hardware for high usage
- ❌ **Backup & Recovery** - Need to backup model configurations

#### 4. **Technical Complexity**
- ❌ **Setup Complexity** - More complex than API key configuration
- ❌ **Model Management** - Need to manage multiple models
- ❌ **Performance Tuning** - May need to tune for optimal performance
- ❌ **Troubleshooting** - Hardware issues can affect LLM availability

#### 5. **Cost Considerations (Hardware)**
- ❌ **Upfront Cost** - Need to purchase/rent GPU servers
- ❌ **Ongoing Costs** - Cloud GPU instances cost $0.50-5.00/hour
- ❌ **Underutilization** - GPU may be idle during low usage periods
- ❌ **Maintenance** - Hardware maintenance and replacement costs

#### 6. **Limited Features**
- ✅ **RAG Implemented** - DevopsMate includes full RAG implementation with Qdrant
- ❌ **No Function Calling** - Some cloud LLMs have better tool/function calling
- ❌ **No Multi-modal** - Limited image/video understanding (though improving)
- ❌ **No Managed Updates** - Need to manually update models

---

## Cost Comparison Example

### Scenario: Medium-Sized DevOps Team
- **Usage**: 5,000 agent queries/month
- **Average**: 500 tokens input, 300 tokens output per query
- **Total**: 2.5M input tokens, 1.5M output tokens/month

### Cloud LLM Costs (OpenAI GPT-4):
```
Input:  2.5M tokens × $0.03/1K = $75/month
Output: 1.5M tokens × $0.06/1K = $90/month
Total:  $165/month = $1,980/year
```

### Cloud LLM Costs (Anthropic Claude):
```
Input:  2.5M tokens × $0.008/1K = $20/month
Output: 1.5M tokens × $0.024/1K = $36/month
Total:  $56/month = $672/year
```

### Ollama Costs:
```
Hardware (Cloud GPU):  $200-500/month (AWS p3.2xlarge)
Hardware (On-prem):    $0-200/month (depreciation)
Electricity:           $20-50/month
Total:                 $20-550/month = $240-6,600/year
```

**Break-even**: At 5,000 queries/month, Ollama pays for itself in **2-4 months** vs OpenAI, **1-2 months** vs Anthropic.

**At 50,000 queries/month**: Ollama saves **$6,000-18,000/year** vs cloud LLMs.

---

## When to Use Ollama vs Cloud LLMs

### ✅ **Use Ollama When:**
- High query volume (1000+ queries/month)
- Sensitive data (code, configs, credentials)
- Compliance requirements (GDPR, HIPAA, SOC 2)
- Cost is a concern
- You have GPU infrastructure
- You need offline capability
- You want full control

### ❌ **Use Cloud LLMs When:**
- Low query volume (< 100 queries/month)
- No GPU infrastructure available
- Need latest model capabilities (GPT-4, Claude 3.5)
- Don't want to manage infrastructure
- Need multi-modal capabilities (vision, audio)
- Budget allows for API costs

---

## Recommended Setup

### For Development:
```bash
# Small model for testing
ollama pull llama3:8b  # ~4GB VRAM
```

### For Production (Small Team):
```bash
# Code-focused model
ollama pull qwen2.5-coder:16b  # ~10GB VRAM
```

### For Production (Enterprise):
```bash
# Best performance models
ollama pull qwen2.5-coder:32b  # ~18GB VRAM - Code tasks
ollama pull mixtral:8x7b       # Analytics tasks
```

### Hardware Recommendations:
- **Minimum**: 16GB RAM, CPU-only (slow but works)
- **Recommended**: 32GB RAM, GPU with 8GB VRAM
- **Optimal**: 64GB RAM, GPU with 16GB+ VRAM (A100, H100)

---

## Conclusion

**Ollama is the perfect fit for DevopsMate because:**

1. ✅ **Cost Efficiency** - Saves thousands per month at scale
2. ✅ **Privacy First** - Aligns with our security-first approach
3. ✅ **Open Source** - Matches our open-source philosophy
4. ✅ **Control** - Full control over LLM operations
5. ✅ **Reliability** - No external dependencies

**The trade-offs (hardware requirements, setup complexity) are worth it for:**
- Enterprise customers with sensitive data
- High-volume usage scenarios
- Cost-conscious organizations
- Compliance-required environments

**For DevopsMate's target market (enterprise observability platform), Ollama provides the best balance of cost, privacy, and control.**

## Installation

### 1. Install Ollama

Visit https://ollama.ai and install Ollama for your operating system.

### 2. Pull Recommended Models

The agent uses intelligent model routing based on task type:

**For Code/Infrastructure Tasks** (Terraform, K8s, code analysis, SSL validation):
```bash
ollama pull qwen2.5-coder:32b     # ~18GB VRAM - Best for code/infra
```

**For Analytics Tasks** (Log analysis, metrics, root cause analysis):
```bash
ollama pull mixtral:8x7b          # Optimized for reasoning/analysis
```

**Alternative models based on hardware:**
```bash
# Smaller code-focused models
ollama pull deepseek-coder-v2:16b  # ~10GB VRAM - Great for code

# General purpose models
ollama pull llama3:70b             # ~40GB VRAM - General purpose
ollama pull llama3:8b              # ~4GB VRAM  - Budget option
```

### 3. Install Python SDK

Ollama uses an OpenAI-compatible API, so we use the OpenAI SDK:

```bash
pip install openai
```

## Configuration

### Environment Variables

```bash
# Ollama base URL (default: http://localhost:11434/v1)
export OLLAMA_BASE_URL="http://localhost:11434/v1"

# Default model (optional, defaults to qwen2.5-coder:32b)
export OLLAMA_MODEL="qwen2.5-coder:32b"

# Code model override (optional)
export OLLAMA_CODE_MODEL="qwen2.5-coder:32b"

# Analytics model override (optional)
export OLLAMA_ANALYTICS_MODEL="mixtral:8x7b"

# Advanced AI - Vector Database & Embeddings (for RAG)
export QDRANT_URL="http://localhost:6333"  # Qdrant vector database URL
export QDRANT_API_KEY=""  # Optional: for Qdrant Cloud
export EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"  # Embedding model
```

### Programmatic Configuration

```python
from agent.llm_service import LLMService, LLMProvider

llm = LLMService(
    provider=LLMProvider.OLLAMA,
    base_url="http://localhost:11434/v1",
)
```

## Model Routing

The agent automatically selects the appropriate model based on task type:

- **Code/Infrastructure tasks** → `qwen2.5-coder:32b`
  - Code analysis
  - Infrastructure (Terraform, K8s)
  - Plan generation
  - Action execution

- **Analytics tasks** → `mixtral:8x7b`
  - Log analysis
  - Metrics analysis
  - Root cause analysis (RCA)
  - Incident management
  - Cost analysis

## Advanced AI - RAG & Knowledge Base

### RAG (Retrieval-Augmented Generation)

RAG enhances LLM responses by retrieving relevant context from your knowledge base before generating answers. This provides:
- **Context-Aware Answers**: Responses based on your actual documentation and incidents
- **Reduced Hallucinations**: Factual context reduces made-up information
- **Historical Learning**: Leverages past incidents and solutions
- **Best Practices**: Incorporates your organization's best practices

### Knowledge Base Types

1. **Incidents**: Historical incidents and their resolutions
2. **Best Practices**: Organization-specific best practices and guidelines
3. **Code Documentation**: Code docs, API documentation, architecture docs
4. **Runbooks**: Operational runbooks and procedures

### How RAG Works

```
User Query → Embed Query → Vector Search (Qdrant) → Retrieve Relevant Chunks → 
Enhance LLM Prompt with Context → Generate Response
```

### Multi-Agent System

Specialized agents for different domains:
- **Metrics Agent**: Specialized in metrics analysis and interpretation
- **Logs Agent**: Specialized in log analysis and pattern detection
- **Security Agent**: Specialized in security analysis and threat detection
- **Cost Agent**: Specialized in cost optimization and resource analysis

**Collaboration Modes:**
- **Sequential**: Agents execute one after another, passing context
- **Parallel**: Agents execute concurrently, results are synthesized
- **Orchestrated**: LLM decides the best execution flow

### Setup RAG & Knowledge Base

1. **Start Qdrant** (vector database):
```bash
docker run -p 6333:6333 qdrant/qdrant
```

2. **Install Python dependencies**:
```bash
pip install qdrant-client sentence-transformers torch transformers
```

3. **Create Knowledge Base** via API:
```bash
curl -X POST http://localhost:8000/api/v1/knowledge-base/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Incident Knowledge Base",
    "description": "Historical incidents and resolutions"
  }'
```

4. **Add Documents** to knowledge base:
```bash
curl -X POST http://localhost:8000/api/v1/knowledge-base/{kb_id}/documents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Database Connection Pool Issue",
    "content": "Issue: Connection pool exhausted...",
    "source_type": "incident"
  }'
```

5. **Query with RAG**:
```bash
curl -X POST http://localhost:8000/api/v1/knowledge-base/rag/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "How do I fix database connection pool exhaustion?",
    "knowledge_base_ids": ["kb-id-1", "kb-id-2"]
  }'
```

### RAG Integration in Agent Modes

- **ASK Mode**: Uses RAG to provide context-aware answers from knowledge base
- **PLAN Mode**: Incorporates best practices and past deployment plans
- **DEBUG Mode**: Retrieves similar past incidents and their resolutions
- **EXECUTE Mode**: Uses historical actions and patterns for safer execution

## Usage Examples

### ASK Mode
```bash
POST /api/v1/agent/query
{
  "query": "How do I set up auto-scaling in AWS ECS?",
  "mode": "ask"
}
```

### PLAN Mode
```bash
POST /api/v1/agent/query/plan
{
  "query": "Deploy a new microservice to Kubernetes with monitoring",
  "scope": "staging"
}
```

### DEBUG Mode
```bash
POST /api/v1/agent/query/debug
{
  "query": "Why is my service returning 500 errors?",
  "code": "def handler(request):\n    return process(request)"
}
```

### EXECUTE Mode
```bash
POST /api/v1/agent/query/execute
{
  "query": "Scale checkout service to 5 replicas",
  "metadata": {
    "approval_token": "approved-abc123"
  }
}
```

## Fallback Behavior

If Ollama is not configured or unavailable, the agent will:
- ASK mode: Use structured handlers for specific queries
- PLAN mode: Return basic plan structure
- DEBUG mode: Use rule-based analysis
- EXECUTE mode: Require explicit action format

## Cost Considerations

- **Ollama**: **FREE** (local models, no API costs)
- Requires GPU for optimal performance (CPU mode available but slower)
- No token limits or usage restrictions
- All processing happens locally on your machine

## Best Practices

1. **GPU Requirements**: For best performance, use a GPU with at least 8GB VRAM
2. **Model Selection**: Use code-focused models (qwen2.5-coder) for infrastructure tasks, analytics models (mixtral) for log/metrics analysis
3. **Temperature Settings**: Lower (0.1-0.3) for factual queries, higher (0.7-1.0) for creative tasks
4. **Cache Responses**: Common queries can be cached to improve response time
5. **Monitor Usage**: Track token usage for monitoring (cost is always $0)
6. **Knowledge Base Maintenance**: Regularly update knowledge base with new incidents and best practices
7. **RAG Context**: Use RAG for queries that benefit from historical context (incidents, best practices)
8. **Multi-Agent Collaboration**: Use multi-agent system for complex queries requiring multiple perspectives
9. **Vector Search Tuning**: Adjust `min_score` threshold (0.7-0.9) to balance relevance vs coverage
10. **Document Chunking**: Ensure documents are properly chunked (1000 chars with 200 char overlap recommended)

## Security

- No API keys required (runs locally)
- All data stays on your machine
- No external API calls
- Log all LLM interactions for audit
- Validate LLM outputs before execution (especially in EXECUTE mode)
- Knowledge base data is tenant-isolated (multi-tenant security)
- Vector embeddings are stored locally in Qdrant (no external vector DB)
- All RAG queries are logged for audit and compliance

## Troubleshooting

### Ollama not running
```bash
# Start Ollama service
ollama serve

# Or on Windows/Mac, Ollama runs as a background service
```

### Model not found
```bash
# List available models
ollama list

# Pull the required model
ollama pull qwen2.5-coder:32b
```

### Connection refused
- Ensure Ollama is running on `http://localhost:11434`
- Check firewall settings
- Verify `OLLAMA_BASE_URL` environment variable

### Qdrant not accessible
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Start Qdrant if not running
docker run -p 6333:6333 qdrant/qdrant
```

### RAG queries returning no results
- Verify knowledge base has documents added
- Check document processing status (should be "ready")
- Lower `min_score` threshold (default 0.7) for more results
- Ensure Qdrant collection exists for the knowledge base

### Embedding generation slow
- Use GPU for sentence-transformers (automatic if CUDA available)
- Consider using smaller embedding model for faster processing
- Batch document processing for better performance
