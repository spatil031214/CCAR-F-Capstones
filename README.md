# Multi-Agent Research Coordinator

A production-ready system that coordinates multiple specialized AI agents to research any topic comprehensively and produce cited reports. Built with the OpenAI API.

## 🎯 Overview

This system demonstrates proper multi-agent architecture with:
- **Explicit context passing** between agents (no implicit inheritance)
- **Proper agentic loop handling** with correct `stop_reason` checking
- **Task decomposition** and parallel/sequential agent coordination
- **Source attribution** with structured citations throughout
- **Graceful error handling** and fallback mechanisms

## 🏗️ Architecture

### Agents

```
Research Topic Input
         ↓
    Coordinator Agent (Task Decomposition)
    ├─→ Web Search Agent (Finds current information)
    ├─→ Document Analysis Agent (Analyzes provided documents)
    ├─→ Fact-Check Agent (Verifies claims)
    └─→ Synthesis Agent (Produces final report)
         ↓
    Final Report (Markdown with Citations)
```

### Agent Responsibilities

| Agent | Purpose | Tools | Output |
|-------|---------|-------|--------|
| **Web Search Agent** | Find current, comprehensive information | `web_search_20260209` | Sources + summaries |
| **Document Analysis Agent** | Extract insights from provided documents | Document parsing | Structured findings |
| **Fact-Check Agent** | Verify claims and cross-reference | `web_search_20260209` | Confidence scores |
| **Synthesis Agent** | Combine all findings into cohesive report | Text generation | Markdown report |

## 🚀 Quick Start

### Installation & Setup

Follow the [SETUP.md](SETUP.md) guide for detailed installation instructions.

**Quick setup:**

```bash
# Install dependencies
pip install -r requirements.txt

# Copy example environment file
cp .env.example .env

# Add your OpenAI API key to .env
# OPENAI_API_KEY=sk-your-actual-key-here
```

### Basic Usage

```bash
# Simple research query
python main.py "What is quantum computing?"

# With focus areas
python main.py "Machine learning advances" \
  --focus-areas "Deep Learning" "Large Language Models" "Efficiency"

# Academic tone with more sources
python main.py "Climate change solutions" \
  --tone academic \
  --max-sources 10

# Analyze documents
python main.py "Healthcare AI trends" \
  --documents-dir ./documents \
  --tone technical

# JSON output
python main.py "Python async programming" \
  --output-format json
```

## 💻 Programmatic Usage

```python
import asyncio
from coordinator import ResearchCoordinator

async def research():
    coordinator = ResearchCoordinator()
    
    report = await coordinator.research(
        topic="Recent advances in biotechnology",
        focus_areas=["CRISPR", "Gene therapy", "Synthetic biology"],
        tone="academic",
        max_sources=8,
    )
    
    # Access report
    print(report.to_markdown())
    
    # Or get structured data
    report_dict = report.to_dict()
    print(report_dict['summary'])
    print(report_dict['citations'])

asyncio.run(research())
```

## 🔄 Agentic Loop Design

Each agent implements proper agentic loop handling:

```python
while iteration < max_iterations:
    response = client.messages.create(
        model=model,
        messages=messages,
        tools=tools,  # e.g., web_search
    )
    
    if response.stop_reason == "tool_use":
        # Execute tool and continue loop
        tool_results = execute_tools(response)
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        
    elif response.stop_reason == "end_turn":
        # Agent finished - extract findings
        return extract_findings(response)
        
    else:
        # Handle other stop reasons (max_tokens, refusal, etc.)
        logger.warning(f"Stop reason: {response.stop_reason}")
        break
```

## 📋 Context Passing Strategy

Agents receive explicit context (no inherited history):

```python
context = ResearchContext(
    topic="Research question",
    focus_areas=["Area 1", "Area 2"],
    tone="academic",
    previous_findings={...},  # From prior agents
    max_sources=5,
)

# Context is serialized and passed to each agent
agent_findings = await agent.research(context)
```

## 🔗 Citation Architecture

### Citation Format

Inline markdown format with bibliography:

```markdown
This is a claim about machine learning [1].

## References

1. [Research Paper Title](https://example.com/paper)
   - Confidence: 95%
   - Accessed: 2026-09-21
   - Snippet: Relevant excerpt from source...
```

### Citation Data Structure

```python
from models.findings import Citation

citation = Citation(
    url="https://example.com/article",
    title="Article Title",
    accessed_date="2026-09-21",
    confidence=0.95,  # 0.0-1.0
    source_type="web",  # web, document, verified
    snippet="Relevant excerpt...",
)
```

## 📊 Data Models

### ResearchContext
Explicit context passed to all agents:
- `topic`: Research question
- `focus_areas`: Priority topics
- `tone`: Report style (academic, business, technical, balanced)
- `previous_findings`: Results from prior agents
- `max_sources`: Source limit

### Citation
Source attribution:
- `url`: Source URL
- `title`: Source title
- `confidence`: Confidence score (0-1)
- `source_type`: Type of source
- `snippet`: Excerpt from source

### Finding
Research finding with attribution:
- `content`: The finding text
- `citations`: List of Citation objects
- `agent`: Which agent produced it
- `confidence`: Confidence score

### ResearchReport
Final synthesized report:
- `topic`: Research topic
- `summary`: Executive summary
- `sections`: Organized report sections
- `findings`: All individual findings
- `all_citations`: Complete bibliography
- `to_markdown()`: Export as markdown
- `to_dict()`: Export as JSON

## 🧪 Testing

### Run Tests

```bash
pytest tests/ -v
pytest tests/test_coordinator.py -k "test_decomposition"
```

### Test Coverage

- `test_coordinator.py`: Task decomposition, agent delegation
- `test_web_search_agent.py`: Web search integration
- `test_document_agent.py`: Document analysis
- `test_fact_check_agent.py`: Verification logic
- `test_synthesis_agent.py`: Report generation

### Integration Test

```python
# End-to-end test
async def test_full_research_flow():
    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="Test topic",
        focus_areas=["Area 1", "Area 2"],
    )
    
    assert report.topic == "Test topic"
    assert len(report.all_citations) > 0
    assert report.summary
```

## 📈 Example: Complete Research Flow

```python
import asyncio
from coordinator import ResearchCoordinator

async def example():
    # Setup
    coordinator = ResearchCoordinator(debug=True)
    
    # Phase 1: Research
    report = await coordinator.research(
        topic="Impact of generative AI on software development",
        focus_areas=[
            "Code generation tools",
            "Developer productivity",
            "Code security implications",
            "Team collaboration changes",
        ],
        tone="technical",
        max_sources=8,
    )
    
    # Phase 2: Export results
    markdown_report = report.to_markdown()
    with open("research_report.md", "w") as f:
        f.write(markdown_report)
    
    # Phase 3: Analyze metrics
    print(f"Citations: {len(report.all_citations)}")
    print(f"Sections: {list(report.sections.keys())}")
    
    # Phase 4: Integrate with other systems
    report_dict = report.to_dict()
    # Send to database, API, etc.

asyncio.run(example())
```

## 🔌 Integration with Capstone

This coordinator can be integrated with the FastAPI Capstone project:

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

@app.get("/research/{topic}")
async def research_get(topic: str):
    report = await coordinator.research(topic=topic)
    return {
        "topic": report.topic,
        "summary": report.summary,
        "markdown": report.to_markdown(),
    }
```

## ⚙️ Configuration

### Environment Variables

```bash
OPENAI_API_KEY=sk-...  # Your OpenAI API key
DEBUG=true             # Enable debug logging
```

### Model Selection

```python
# Use GPT-4 Turbo (default, recommended for reasoning)
coordinator = ResearchCoordinator(model="gpt-4-turbo")

# Use GPT-4 (more capable, higher cost)
coordinator = ResearchCoordinator(model="gpt-4")

# Use GPT-3.5 Turbo (fastest, cheapest)
coordinator = ResearchCoordinator(model="gpt-3.5-turbo")
```

## 📊 Performance & Cost

### Token Usage (Typical Research)

| Phase | Tokens | Cost |
|-------|--------|------|
| Web Search (3 searches) | 2,000 | ~$0.01 |
| Document Analysis | 3,000 | ~$0.015 |
| Fact-Checking | 1,500 | ~$0.01 |
| Synthesis | 2,000 | ~$0.01 |
| **Total** | **8,500** | **~$0.15** |

*Costs estimated with GPT-4 Turbo pricing*

### Optimization Tips

1. **Use GPT-3.5 Turbo** for simple queries (1/4 the cost of GPT-4)
2. **Limit max_sources** to reduce token usage
3. **Batch multiple queries** if possible
4. **Monitor token usage** via OpenAI dashboard

## 🛠️ Development

### Project Structure

```
research-coordinator/
├── coordinator.py           # Main orchestrator
├── agents/
│   ├── web_search_agent.py
│   ├── document_agent.py
│   ├── fact_check_agent.py
│   └── synthesis_agent.py
├── models/
│   ├── context.py
│   └── findings.py
├── utils/
│   ├── citations.py
│   ├── loop_handler.py
├── tests/
│   ├── test_coordinator.py
│   ├── test_agents.py
│   └── test_findings.py
├── requirements.txt
├── README.md
└── main.py
```

### Adding New Agents

```python
# 1. Create agents/my_agent.py
class MyAgent:
    async def research(self, context: ResearchContext):
        return {"findings": "...", "citations": [...]}

# 2. Register in coordinator.py
self.my_agent = MyAgent(self.client, self.model)

# 3. Call in research flow
results = await self.my_agent.research(context)
```

## 🔒 Security Considerations

- API keys should be in environment variables, never hardcoded
- Document analysis works with local files only
- Content filtering is applied to search results
- All citations include source URLs for verification
- Sensitive information in documents is not logged

## 📝 Logging

The system includes comprehensive logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Or enable debug logging
coordinator = ResearchCoordinator(debug=True)
```

Log levels:
- `DEBUG`: Detailed loop iterations, tool calls
- `INFO`: Phase completion, agent status
- `WARNING`: Failed operations, fallbacks
- `ERROR`: Critical failures

## 🤝 Contributing

To extend or modify the system:

1. Add new agents in `agents/` directory
2. Extend data models in `models/`
3. Add tests in `tests/`
4. Update documentation
5. Test end-to-end with `pytest tests/`

## 📄 License

This project is provided as an example implementation of multi-agent coordination with OpenAI.

## 🆘 Troubleshooting

### API Key Issues
```bash
export OPENAI_API_KEY="sk-..."
python -c "from openai import OpenAI; OpenAI()"
```

### Agent Timeouts
Increase max iterations or use faster model:
```python
coordinator = ResearchCoordinator(model="gpt-3.5-turbo")
```

### Low Citation Count
Increase max_sources or expand focus_areas:
```python
report = await coordinator.research(
    topic="...",
    max_sources=10,  # Increased from default 5
)
```

## 📚 References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Models](https://platform.openai.com/docs/models)
- [Chat Completions Guide](https://platform.openai.com/docs/guides/gpt)

---

**Built with GPT-4 Turbo and the OpenAI API**
