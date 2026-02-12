# Stack Research

**Domain:** AI Agent Metacognition / Comprehension Systems
**Researched:** 2026-02-13
**Confidence:** MEDIUM-HIGH

## Executive Summary

Building a "Comprehension-as-Code" system requires a stack optimized for:
1. **Knowledge representation** - Structured, versioned, human+AI readable formats
2. **Belief tracking** - Bayesian updates in natural language with probabilistic foundations
3. **Agent observation** - Tracing, logging, and learning from agent execution
4. **Memory persistence** - Episodic, semantic, and procedural memory across sessions

The recommended stack prioritizes **simplicity over sophistication**: Markdown+YAML for knowledge representation, Pydantic for schema validation, SQLite+ChromaDB for persistence, and LangGraph for agent orchestration with LangSmith for observation.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **Python** | 3.11+ | Primary language | Universal AI/ML support, type hints maturity, ecosystem breadth | HIGH |
| **LangGraph** | 1.0.8 | Agent orchestration | Production-ready state machines, durable execution, human-in-the-loop, built-in checkpointing. Trusted by Klarna, Replit, Elastic. | HIGH |
| **Pydantic** | 2.x / PydanticAI 1.58.0 | Schema validation | Powers validation in OpenAI SDK, Anthropic SDK, LangChain, etc. 300M+ monthly downloads. Type-safe structured outputs with automatic retries. | HIGH |
| **ChromaDB** | 1.5.0 | Vector storage | Simple API, Rust-core rewrite (4x performance), native LangChain integration, persistence to disk. Ideal for semantic memory. | HIGH |
| **SQLite** + **sqlite-vec** | 0.1.6+ | Relational + vector | Zero-ops local-first persistence. Combines FTS5 (full-text), sqlite-vec (vector), and standard SQL. Perfect for episodic/procedural memory. | MEDIUM-HIGH |

### Knowledge Representation Layer

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **Markdown + YAML frontmatter** | N/A | Primary knowledge format | Human-readable, git-friendly, token-efficient, AI-preferred format. Emerging standards (AGENTS.md, SKILL.md, Markform). | HIGH |
| **Pydantic models** | 2.x | Schema definition | Define comprehension structures as typed Python classes. Automatic JSON Schema generation for LLM prompting. | HIGH |
| **JSONL** | N/A | Event logging | Append-only, streamable, natural for temporal sequences of observations/updates. | HIGH |

### Belief Tracking & Probabilistic Reasoning

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **pgmpy** | 1.0.0 | Bayesian networks | Mature, well-documented library for DAGs, Bayesian Networks, causal inference. Ideal for explicit belief graph structures. | HIGH |
| **NumPyro** | 0.20.0 | Probabilistic programming | JAX-powered, 100x faster than alternatives for MCMC. Best for learning posteriors when you need real probabilistic inference. | MEDIUM |
| **Natural language Bayes** | N/A | Comprehension format | For MVP: Express priors/posteriors/observations in structured Markdown. Formal inference can be added incrementally. | HIGH |

### Agent Observation & Learning

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **LangSmith** | Latest | Observability | Purpose-built for LangGraph. Zero-config tracing, thread visualization, multi-turn evals, Insights Agent for pattern discovery. | HIGH |
| **Reflexion pattern** | N/A | Self-improvement | Proven technique: verbal reinforcement learning. 18%+ accuracy improvement through self-reflection on mistakes. | MEDIUM-HIGH |
| **DSPy** | 3.1.3 | Programmatic LLM modules | Alternative to prompt engineering. Declarative signatures, automatic optimization. Good for systematic comprehension extraction. | MEDIUM |

### Memory Systems

| Technology | Version | Purpose | When to Use | Confidence |
|------------|---------|---------|-------------|------------|
| **ChromaDB** | 1.5.0 | Semantic memory | Facts, concepts, accumulated knowledge. Vector similarity for retrieval. | HIGH |
| **SQLite + FTS5** | Latest | Episodic memory | Event logs, conversation history, temporal queries. Full-text + structured. | HIGH |
| **Markdown files** | N/A | Procedural memory | Agent instructions, learned patterns, comprehension artifacts. Git-versioned. | HIGH |
| **Graphiti** | Latest | Temporal knowledge graph | When relationships matter: who learned what from whom, belief provenance. Requires Neo4j. | LOW-MEDIUM |

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| **Instructor** | 1.14.5 | Structured extraction | Simpler alternative to PydanticAI for quick structured LLM outputs. | HIGH |
| **PyYAML** | 6.x | YAML parsing | Loading/dumping comprehension documents. | HIGH |
| **python-frontmatter** | 1.x | Markdown+YAML | Parsing Markdown files with YAML frontmatter. | HIGH |
| **rich** | 13.x | Terminal output | Debugging, status display for meta-agent observation. | MEDIUM |
| **watchdog** | 4.x | File monitoring | Triggering comprehension updates when files change. | MEDIUM |

---

## Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **uv** | Package management | Faster than pip, poetry. Single lockfile. Recommended by Python community in 2025. |
| **ruff** | Linting + formatting | Replaces black, isort, flake8. 10-100x faster. |
| **pytest** | Testing | Standard. Use with pytest-asyncio for async agents. |
| **pre-commit** | Git hooks | Enforce formatting, type checking before commit. |
| **mypy** | Type checking | Strict mode for Pydantic model validation. |

---

## Installation

```bash
# Core (using uv)
uv pip install langgraph langsmith pydantic-ai chromadb

# Bayesian reasoning
uv pip install pgmpy numpyro jax jaxlib

# Knowledge representation
uv pip install pyyaml python-frontmatter

# Structured LLM output (alternative to pydantic-ai)
uv pip install instructor

# SQLite vector extension
uv pip install sqlite-vec

# Development
uv pip install pytest pytest-asyncio ruff mypy pre-commit rich watchdog
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **LangGraph** | CrewAI | When you want simpler multi-agent setup with less control. CrewAI is more opinionated, faster to prototype. |
| **LangGraph** | AutoGen | When Microsoft ecosystem integration matters. AutoGen 0.4 has improved but LangGraph is more mature. |
| **LangGraph** | DSPy only | When you don't need stateful agents, just optimized LLM pipelines. DSPy excels at prompt optimization. |
| **ChromaDB** | Weaviate | When you need multi-tenancy, enterprise features, or GraphQL API. More complex to operate. |
| **ChromaDB** | Pinecone | When you need managed cloud vector DB. Good for scale, but vendor lock-in and cost. |
| **SQLite** | PostgreSQL + pgvector | When you need multi-user concurrency or are already on Postgres. More operational complexity. |
| **pgmpy** | PyMC 5.27.1 | When you need MCMC sampling for complex posteriors. PyMC is more powerful but heavier. |
| **Markdown** | JSON-LD | When you need semantic web interoperability. Much more complex, less human-readable. |
| **PydanticAI** | Instructor | Instructor is simpler for quick extraction. PydanticAI is better for full agent development. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **LangChain (chains)** | Deprecated pattern. Abstractions leaked, hard to debug. LangChain team now recommends LangGraph. | LangGraph for stateful flows, direct SDK calls for simple cases |
| **sqlite-vss** | Deprecated. No longer in active development. | sqlite-vec (successor) |
| **Pinecone/Weaviate for MVP** | Over-engineering for local-first comprehension system. Operational complexity not justified. | ChromaDB or SQLite+sqlite-vec |
| **Custom observation infrastructure** | Build vs buy. LangSmith handles this well. | LangSmith (free tier: 5,000 traces/month) |
| **XML for knowledge representation** | Verbose, not token-efficient, poor AI comprehension. | Markdown + YAML |
| **MongoDB** | Schema-less leads to drift. Comprehension needs structure. | SQLite (typed) + Pydantic (validated) |
| **OpenAI Assistants API** | Vendor lock-in, opaque state management, limited customization. | LangGraph with any LLM provider |
| **BabyAGI / AutoGPT patterns** | Early 2023 patterns, superseded by proper agent frameworks. | LangGraph or PydanticAI |

---

## Stack Patterns by Variant

**If primary consumer is AI agents bootstrapping from comprehension:**
- Use Markdown+YAML as primary format (token-efficient, parseable)
- Store in git for versioning and diff-ability
- Index in ChromaDB for semantic retrieval
- Generate JSON Schema from Pydantic models for LLM prompting

**If belief tracking needs formal probabilistic inference:**
- Add pgmpy for Bayesian network structure
- Use NumPyro for posterior sampling when needed
- Keep natural language representation as the primary interface
- Formal inference as optional "reasoning backend"

**If learning from mistakes is critical:**
- Implement Reflexion pattern via LangGraph
- Store error episodes in SQLite (episodic memory)
- Use LangSmith Insights Agent for pattern discovery
- Extract learnings to Markdown (procedural memory)

**If temporal relationships matter:**
- Add Graphiti for temporal knowledge graph
- Requires Neo4j dependency (more operational complexity)
- Worth it for: belief provenance, "when did we learn X?"
- Consider: start with JSONL timestamps, add Graphiti if needed

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| LangGraph 1.0.x | Python 3.10+ | Dropped Python 3.9 support in v1.0 |
| PydanticAI 1.x | Pydantic 2.x | Does NOT work with Pydantic 1.x |
| ChromaDB 1.x | Python 3.9-3.12 | Rust core requires compatible wheel |
| NumPyro 0.20.x | JAX 0.4.x | Install jax/jaxlib before numpyro |
| pgmpy 1.0.x | Python 3.9+ | Stable 1.0 release (March 2025) |
| DSPy 3.x | Python 3.10+ | Major API changes from 2.x |

---

## Architecture Recommendation for Comprehension-as-Code

```
                    ┌─────────────────────────────────────┐
                    │         Knowledge Layer             │
                    │  Markdown+YAML comprehension files  │
                    │       (git-versioned, indexed)      │
                    └─────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │   ChromaDB   │ │    SQLite    │ │   Markdown   │
           │  (semantic)  │ │ (episodic)   │ │ (procedural) │
           └──────────────┘ └──────────────┘ └──────────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌─────────────────────────────────────┐
                    │          Meta-Agent (LangGraph)     │
                    │   Observes → Extracts → Validates   │
                    │        → Updates Comprehension      │
                    └─────────────────────────────────────┘
                                     │
                    ┌─────────────────────────────────────┐
                    │          Working Agent(s)           │
                    │  Bootstrap from comprehension files │
                    │    Report observations back up      │
                    └─────────────────────────────────────┘
                                     │
                    ┌─────────────────────────────────────┐
                    │          LangSmith Observability    │
                    │   Traces → Patterns → Learnings     │
                    └─────────────────────────────────────┘
```

---

## MVP Stack (Minimal Viable Implementation)

For first iteration, start with:

```bash
uv pip install langgraph langsmith pydantic chromadb pyyaml python-frontmatter
```

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Agent orchestration | LangGraph | Production-ready, built-in persistence |
| Knowledge format | Markdown + YAML | Human+AI readable, git-friendly |
| Validation | Pydantic | Type safety, schema generation |
| Semantic memory | ChromaDB | Simple setup, good enough performance |
| Episodic memory | SQLite | Zero-ops, built into Python |
| Observation | LangSmith | Free tier sufficient for development |

Add incrementally as needed:
- pgmpy when belief graph structure becomes complex
- NumPyro when you need actual posterior sampling
- Graphiti when temporal provenance matters
- DSPy when prompt optimization becomes bottleneck

---

## Sources

### High Confidence (Official Docs, PyPI)
- [LangGraph 1.0.8](https://pypi.org/project/langgraph/) - PyPI, February 2026
- [PydanticAI 1.58.0](https://pypi.org/project/pydantic-ai/) - PyPI, February 2026
- [ChromaDB 1.5.0](https://pypi.org/project/chromadb/) - PyPI, February 2026
- [Instructor 1.14.5](https://pypi.org/project/instructor/) - PyPI, January 2026
- [pgmpy 1.0.0](https://pypi.org/project/pgmpy/) - PyPI, March 2025
- [NumPyro 0.20.0](https://pypi.org/project/numpyro/) - PyPI, January 2026
- [PyMC 5.27.1](https://pypi.org/project/pymc/) - PyPI, January 2026
- [DSPy 3.1.3](https://github.com/stanfordnlp/dspy/releases) - GitHub, February 2025

### Medium Confidence (Official Blogs, Documentation)
- [LangGraph Overview](https://www.langchain.com/langgraph) - LangChain official
- [LangSmith Observability](https://www.langchain.com/langsmith/observability) - LangChain official
- [LangChain and LangGraph 1.0](https://blog.langchain.com/langchain-langgraph-1dot0/) - LangChain blog
- [Model Context Protocol](https://modelcontextprotocol.io/) - Anthropic official
- [Pydantic AI](https://ai.pydantic.dev/) - Pydantic official
- [Graphiti by Zep](https://github.com/getzep/graphiti) - GitHub
- [sqlite-vec](https://github.com/asg017/sqlite-vec) - GitHub

### Medium Confidence (Research Papers, Verified Sources)
- [Zep Temporal Knowledge Graph Architecture](https://arxiv.org/abs/2501.13956) - arXiv, January 2025
- [Self-Reflection in LLM Agents](https://arxiv.org/abs/2405.06682) - arXiv
- [Multi-Agent Reflexion (MAR)](https://arxiv.org/html/2512.20845) - arXiv, December 2025
- [Memory in the Age of AI Agents Survey](https://github.com/Shichun-Liu/Agent-Memory-Paper-List) - GitHub

### WebSearch (Verified with Multiple Sources)
- [Best AI Agent Frameworks 2025](https://langwatch.ai/blog/best-ai-agent-frameworks-in-2025-comparing-langgraph-dspy-crewai-agno-and-more) - LangWatch
- [AGENTS.md Standard](https://www.builder.io/blog/agents-md) - Builder.io
- [Agent Skills Standard](https://nayakpplaban.medium.com/agent-skills-standard-for-smarter-ai-bde76ea61c13) - Medium
- [MCP Joins Agentic AI Foundation](https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/) - MCP Blog, December 2025

---

*Stack research for: Comprehension-as-Code AI Agent System*
*Researched: 2026-02-13*
