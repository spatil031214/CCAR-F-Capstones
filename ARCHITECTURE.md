# Research Coordinator - Architecture & Design Patterns

## Overview

This document explains the architectural decisions, design patterns, and implementation details of the Multi-Agent Research Coordinator system.

## 1. Multi-Agent Orchestration Pattern

### Coordinator-Subagent Model

The system uses a **hierarchical coordinator-subagent pattern**:

```
┌─────────────────────────────────────┐
│      Research Coordinator           │
│  (Task Decomposition & Synthesis)   │
└────────────┬────────────────────────┘
             │
    ┌────────┼────────┬─────────┐
    ▼        ▼        ▼         ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌─────────┐
│ Web    │ │ Doc  │ │ Fact   │ │Synthesis│
│Search  │ │ Anal │ │Check   │ │ Agent   │
│Agent   │ │sis   │ │Agent   │ │         │
└────────┘ └──────┘ └────────┘ └─────────┘
```

### Execution Flow

**Sequential Execution** (not parallel):

1. **Coordinator** receives research topic
2. **Web Search Agent** → Finds current information
3. **Document Analysis Agent** → Analyzes provided documents (optional)
4. **Fact-Check Agent** → Verifies claims from phases 1-2
5. **Synthesis Agent** → Produces final report

Each agent completes before the next begins, allowing context to flow forward.

### Why Sequential?

- Agents can use prior findings for enhanced context
- Reduces redundant searching/analysis
- Clearer error handling and debugging
- Easier to track data lineage and citations

For parallel execution, spawn independent coordinators with isolated contexts.

## 2. Agentic Loop Design

### Stop Reason Handling

The core of each agent is the agentic loop that **correctly handles `stop_reason`**:

```python
while iteration < max_iterations:
    response = client.messages.create(
        model=model,
        messages=messages,
        tools=tools,
    )
    
    if response.stop_reason == "tool_use":
        # Agent wants to use a tool
        # 1. Execute all tool calls in parallel
        # 2. Append assistant message to history
        # 3. Append tool results to history
        # 4. Continue loop
        
    elif response.stop_reason == "end_turn":
        # Agent has finished
        # 1. Extract findings from response
        # 2. Return results
        # 3. Break loop
        
    else:
        # Other stop reasons (max_tokens, refusal, etc.)
        # 1. Log warning
        # 2. Return partial results
        # 3. Break loop
```

### Key Points

1. **Tool use handling** (Provider-specific): 
   - Tool call is requested but NOT executed by the server
   - Agent **expects** the client to execute the tool
   - Results must be appended as `tool_result` blocks
   - Note: OpenAI implementation simplified to use direct API calls without tool execution

2. **`stop_reason == "end_turn"`**:
   - Agent has completed its reasoning
   - No tool calls are pending
   - Safe to extract final findings

3. **Message Structure**:
   - **Assistant messages**: Contain agent's text and tool calls
   - **User messages**: Contain tool results (when responding to tool calls)
   - Alternating pattern maintains conversation history

### Implementation (Web Search Agent)

```python
async def research(self, context: ResearchContext) -> Dict:
    messages = [{"role": "user", "content": "Research this topic..."}]
    tools = [{"type": "web_search_20260209", "name": "web_search"}]
    
    iteration = 0
    while iteration < max_iterations:
        response = client.messages.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )
        
        if response.stop_reason == "tool_use":
            # Process tool calls
            for block in response.content:
                if block.type == "tool_use":
                    # Tool execution handled differently per provider
                    # We receive results in next turn
                    pass
            
            # Add assistant message
            messages.append({
                "role": "assistant",
                "content": response.content,
            })
            
            # Add tool result placeholders
            messages.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": ..., "content": "..."}
                ],
            })
            
        elif response.stop_reason == "end_turn":
            # Extract findings and return
            return extract_findings(response)
```

## 3. Explicit Context Passing

### ResearchContext Design

Rather than inheriting conversation history, agents receive **explicit context**:

```python
@dataclass
class ResearchContext:
    topic: str                          # Research question
    focus_areas: List[str]              # Priority topics
    tone: str                           # Report style
    max_sources: int                    # Source limit
    previous_findings: Dict[str, Any]   # Results from prior agents
    include_document_analysis: bool     # Include doc analysis?
    document_paths: List[str]           # Document locations
```

### Advantages

1. **No Hidden State**: All context is visible in method signatures
2. **Composability**: Agents can be used independently with full context
3. **Traceability**: Easy to audit what information each agent received
4. **Testability**: Context can be mocked for unit tests
5. **Reusability**: Agents don't depend on coordinator's history

### Flow Example

```python
# Phase 1: Web Search Agent
context = ResearchContext(topic="AI Ethics", focus_areas=["Bias", ...])
web_findings = await web_agent.research(context)

# Phase 2: Document Analysis Agent
# Update context with prior findings
context.previous_findings = {"web_search": web_findings["findings"]}
doc_findings = await doc_agent.research(context)

# Phase 3: Fact-Check Agent
# Previous findings available for verification
fact_check_results = await fact_check_agent.verify(context, combined)
```

### Message Construction from Context

Each agent converts context to a prompt:

```python
def build_system_prompt(context: ResearchContext) -> str:
    system = f"Research topic: {context.topic}\n"
    
    if context.focus_areas:
        system += f"Focus areas:\n"
        for area in context.focus_areas:
            system += f"  - {area}\n"
    
    if context.previous_findings:
        system += f"Use these prior findings:\n"
        for key, value in context.previous_findings.items():
            system += f"  - {key}: {value}\n"
    
    return system
```

## 4. Citation Architecture

### Citation Data Model

```python
@dataclass
class Citation:
    url: str                    # Source URL
    title: str                  # Source title
    accessed_date: Optional[str]  # When accessed
    confidence: float           # 0.0-1.0 confidence score
    source_type: str            # "web", "document", "verified"
    snippet: str                # Excerpt from source
```

### Citation Preservation

Each agent **attaches citations to findings**:

```python
finding = Finding(
    content="Machine learning improves diagnostic accuracy by 15%",
    citations=[
        Citation(
            url="https://doi.org/...",
            title="ML in Medical Imaging Study",
            confidence=0.95,
        )
    ],
    agent="Web Search Agent",
    confidence=0.9,
)
```

### Citation Aggregation

The synthesis agent collects citations from all sources:

```python
class ResearchReport:
    all_citations: List[Citation] = []
    
    def add_finding(self, finding: Finding):
        self.findings.append(finding)
        for citation in finding.citations:
            if citation.url not in seen_urls:
                self.all_citations.append(citation)
```

### Bibliography Generation

Final report includes formatted bibliography:

```markdown
## References

1. [ML in Medical Imaging Study](https://doi.org/...)
   - Confidence: 95%
   - Accessed: 2026-09-21
   - Snippet: Machine learning models achieved...
```

## 5. Tool Use Architecture

### Server-Side Tools

The system uses **API-based operations** with proper context management:

```python
tools = [
    {
        "type": "web_search_20260209",  # Dynamic web search
        "name": "web_search",
    }
]
```

**Advantages**:
- No client-side execution overhead
- Automatic result handling
- Built-in SafeSearch filtering
- Cost-efficient (results are server-processed)

### Tool Result Processing

When a tool is used:

```python
# Step 1: Agent requests tool use
if response.stop_reason == "tool_use":
    # Step 2: Find tool use blocks
    for block in response.content:
        if block.type == "tool_use":
            tool_id = block.id
            tool_name = block.name
            tool_input = block.input
    
    # Step 3: Tool is executed by server (in next API call)
    # Step 4: We append tool_result block
    tool_results = [
        {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": "Tool result content..."
        }
    ]
    
    # Step 5: Continue loop with results
    messages.append({"role": "user", "content": tool_results})
```

## 6. Error Handling & Graceful Degradation

### Per-Agent Error Handling

Each agent has try-catch:

```python
try:
    results = await agent.research(context)
    agent_reports[agent_name] = results
except Exception as e:
    logger.error(f"Agent {agent_name} failed: {e}")
    agent_reports[agent_name] = {
        "status": "failed",
        "error": str(e),
        "findings": "",
    }
```

### Coordinator-Level Fallbacks

```python
# Phase 1: Web Search - critical
web_results = await web_search_agent.research(context)
if web_results["status"] == "failed":
    logger.warning("Web search failed, continuing with other agents")

# Phase 2: Document Analysis - optional
if documents:
    doc_results = await doc_agent.research(context)
    if doc_results["status"] == "failed":
        logger.warning("Doc analysis failed, using web results only")

# Phase 3: Fact-Checking - optional
fact_check_results = await fact_check_agent.verify(context, findings)

# Phase 4: Synthesis - always runs
final_report = await synthesis_agent.synthesize(context, agent_reports)
# Includes partial findings even if some agents failed
```

### Status Tracking

Each phase reports its status:

```python
return {
    "agent": "Web Search Agent",
    "status": "completed",  # or "failed", "skipped"
    "findings": "...",
    "citations": [...],
    "error": None,  # Error message if status is "failed"
}
```

## 7. Performance Optimization

### Token Management

**Per-request limits**:
- Web Search: 2,000 tokens (3 searches)
- Document Analysis: 3,000 tokens (depends on doc size)
- Fact-Checking: 1,500 tokens (verification searches)
- Synthesis: 2,000 tokens (final report)
- **Total**: ~8,500 tokens ≈ $0.045 (Opus 5 pricing)

**Optimization strategies**:
1. Use `prompt_caching` for repeated topics
2. Limit `max_sources` parameter
3. Use smaller models for subagents if appropriate
4. Implement task budgets for long-running queries

### Async Execution

```python
async def research(self, context: ResearchContext):
    # All I/O is async, no blocking
    response = await self.client.messages.create_async(...)
    # Non-blocking processing
```

### Parallel Agent Support (Future)

For parallel execution of independent agents:

```python
# Run agents without dependencies in parallel
web_task = web_agent.research(context)
doc_task = doc_agent.research(context)  # Independent copy of context

results = await asyncio.gather(web_task, doc_task)
```

## 8. Integration Points

### FastAPI Integration

```python
from fastapi import FastAPI
from coordinator import ResearchCoordinator

app = FastAPI()
coordinator = ResearchCoordinator()

@app.post("/research")
async def research_endpoint(topic: str, focus_areas: list = None):
    report = await coordinator.research(
        topic=topic,
        focus_areas=focus_areas,
    )
    return report.to_dict()
```

### LLM Evaluation Framework

The system can integrate with evaluation frameworks:

```python
# For capstone's golden question set
for question in golden_questions:
    report = await coordinator.research(question["query"])
    # Compare report.summary to expected_answer
    # Measure citation accuracy
    # Calculate coverage score
```

## 9. Testing Strategy

### Unit Tests
- Context creation and serialization
- Citation deduplication
- Finding creation
- Report generation

### Integration Tests
- End-to-end research flow
- Citation preservation across agents
- Stop reason handling
- Error recovery

### Mock Testing
- Mock agent responses
- Simulate tool call failures
- Test message construction

## 10. Extension Points

### Adding New Agents

```python
class CustomAgent:
    async def research(self, context: ResearchContext) -> Dict:
        # Implement agentic loop
        # Return structured findings
        return {
            "agent": "Custom Agent",
            "findings": "...",
            "citations": [...],
            "status": "completed",
        }

# Register in coordinator
self.custom_agent = CustomAgent(self.client, self.model)

# Call in research flow
results = await self.custom_agent.research(context)
```

### Custom Tool Integration

```python
# Add custom tools alongside server tools
tools = [
    {"type": "web_search_20260209", "name": "web_search"},
    {
        "type": "function",
        "name": "query_database",
        "description": "Query internal database",
        "input_schema": {...},
    }
]
```

---

**Key Takeaways**:
1. ✅ Coordinator orchestrates sequential agents
2. ✅ Each agent has proper agentic loop with stop_reason handling
3. ✅ Explicit context passing between agents
4. ✅ Full citation chain from source to final report
5. ✅ Graceful error handling and degradation
6. ✅ Extensible for new agents and tools
