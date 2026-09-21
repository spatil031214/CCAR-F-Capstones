# Citation Preservation Analysis

## Executive Summary

**Current Status: ❌ CITATIONS ARE NOT PROPERLY PRESERVED**

The current implementation loses source attribution during synthesis. While citations are collected, they are:
- Not embedded inline in the synthesized report text
- Disconnected from specific claims
- Listed only in a "Sources" section without context

This violates academic integrity principles where readers should know which claim comes from which source.

---

## The Problem

### 1. Web Search Agent: Empty Citations List

**File:** `agents/web_search_agent.py` (lines 87-93)

```python
return {
    "agent": self.name,
    "topic": context.topic,
    "findings": findings_text,
    "citations": all_citations,  # ← ALWAYS EMPTY!
    "status": "completed",
}
```

**Issue:**
- `all_citations = []` is initialized but never populated
- The imported function `extract_citations_from_web_search()` is **never used**
- Web search findings lose all source information

### 2. Missing Inline Citations in Final Report

**File:** `models/findings.py` (lines 77-97)

```python
def to_markdown(self) -> str:
    markdown = f"# {self.topic}\n\n"
    markdown += f"{self.summary}\n\n"
    
    if self.sections:
        for section_name, content in self.sections.items():
            markdown += f"## {section_name}\n\n"
            markdown += f"{content}\n\n"  # ← No inline citations here
    
    # Bibliography added at end (disconnected from claims)
    if self.all_citations:
        markdown += "## Sources\n\n"
        for i, citation in enumerate(self.all_citations, 1):
            markdown += f"{i}. [{citation.title}]({citation.url})\n"
```

**Issue:**
- Report text has NO inline citations like `[1]`, `[2]`
- Claims and sources are completely disconnected
- Readers can't tell which source supports which claim

### 3. Limited Document Citation Extraction

**File:** `agents/document_agent.py` (lines 90-99)

```python
for doc in documents:
    if doc.get("path") in findings_text or doc.get("name") in findings_text:
        # Only creates citation if document name appears in text
        citation = Citation(...)
```

**Issue:**
- Only cites documents if their name is mentioned
- Many referenced claims don't get cited
- Loose matching (string search) is unreliable

### 4. Citation Loss in Synthesis

**File:** `agents/synthesis_agent.py` (lines 133-151)

The synthesis agent:
1. Takes the synthesized text (which has no inline citations)
2. Collects citations from agent reports (which are mostly empty)
3. Adds them to a bibliography section

Result: Claims in the final report are **orphaned** - no source attribution.

---

## Visual Example of the Problem

### Input Findings (With Citations):
```
AI has revolutionized healthcare [Nature Medicine, 2024].
Machine learning improves diagnosis [Google Health, 2024].
```

### Output Final Report (Lost Citations):
```
# Healthcare AI

AI has revolutionized healthcare.
Machine learning improves diagnosis.

## Sources
1. Nature Medicine
2. Google Health
```

**Problem:** Readers don't know which claim uses which source! ❌

---

## The Solution

Two improved agents are provided:

### 1. WebSearchAgentV2 (`agents/web_search_agent_v2.py`)

**Improvements:**
```python
# Instructs the LLM to include inline citations
system_prompt = """...
For EVERY claim you make, include the source:
- Use [Source Name, Year] inline
- Example: "AI revolutionized healthcare [Nature Medicine, 2024]"
..."""

# Extracts citations from the text
citations = self._extract_citations_from_text(findings_text)
```

**Features:**
- ✅ Requests inline citations from the LLM
- ✅ Extracts [Source, Year] patterns
- ✅ Extracts URLs from text
- ✅ Returns citations with findings

### 2. SynthesisAgentV2 (`agents/synthesis_agent_v2.py`)

**Improvements:**
```python
# Explicitly preserves citations during synthesis
system_prompt = """...
CRITICAL: PRESERVE ALL inline citations from source findings [Source, Year]
EVERY claim must have a source attribution
..."""

# Preserves inline citations in final report
report.add_section("Full Report", synthesis_text)  # With [Citations]
```

**Features:**
- ✅ Instructs LLM to preserve inline citations
- ✅ Lists all available citations for reference
- ✅ Extracts additional citations from synthesis
- ✅ Deduplicates citations properly

---

## Implementation Comparison

| Feature | Current | V2 (Improved) |
|---------|---------|---------------|
| **Web Search Citations** | ❌ Empty list | ✅ Extracted from text |
| **Inline Citations** | ❌ None | ✅ [Source, Year] format |
| **Citation Extraction** | ❌ Unused function | ✅ Active extraction |
| **Source-Claim Link** | ❌ Broken | ✅ Inline attribution |
| **Bibliography** | ✅ Exists | ✅ Enhanced |
| **Academic Integrity** | ❌ Poor | ✅ Proper |

---

## How to Use Improved Versions

### Option 1: Replace agents in coordinator.py

```python
from agents.web_search_agent_v2 import WebSearchAgentV2
from agents.synthesis_agent_v2 import SynthesisAgentV2

class ResearchCoordinator:
    def __init__(self, ...):
        self.web_search_agent = WebSearchAgentV2(self.client, model)
        self.synthesis_agent = SynthesisAgentV2(self.client, model)
        # Other agents unchanged
```

### Option 2: Run improved versions standalone

```bash
python agents/web_search_agent_v2.py
python agents/synthesis_agent_v2.py
```

---

## Citation Format in Improved Version

### In Findings Text:
```
Recent advancements in AI include GPT-4 [OpenAI, 2024] and improved 
robotic surgery systems [Science Robotics, 2024]. These developments 
show significant improvement [Nature Medicine, 2024] in multiple domains.
```

### In Final Report (Preserved):
```
Recent advancements in AI include GPT-4 [OpenAI, 2024] and improved 
robotic surgery systems [Science Robotics, 2024]. These developments 
show significant improvement [Nature Medicine, 2024] in multiple domains.

## Sources
1. OpenAI, 2024
2. Science Robotics, 2024
3. Nature Medicine, 2024
```

Now readers see exactly which claim uses which source! ✅

---

## Recommendations

### Immediate (Fix Current Issues)
1. ✅ Use WebSearchAgentV2 for proper citation extraction
2. ✅ Use SynthesisAgentV2 to preserve inline citations
3. ✅ Update system prompts to enforce inline citations

### Medium-term (Enhance Quality)
1. Implement numeric citation format `[1]`, `[2]` with footnotes
2. Add confidence scores to citations in final report
3. Highlight conflicting sources with different viewpoints

### Long-term (Academic Standard)
1. Support BibTeX/CSL JSON formats
2. Add citation verification system
3. Generate automated bibliography in multiple formats

---

## Example Output Comparison

### Current Version Output:
```
# Impact of AI on Healthcare

AI is transforming healthcare through multiple avenues...
[Content with NO inline citations]

## Sources
1. Nature Medicine
2. Google Health
3. Tesla
```

### V2 Improved Output:
```
# Impact of AI on Healthcare

AI is transforming healthcare [Nature Medicine, 2024] through diagnostics 
[Google Health, 2024], robotics [Science Robotics, 2023], and autonomous 
systems [Tesla, 2024]. Each of these domains shows measurable improvement 
[Nature Medicine, 2024].

## Sources
1. Nature Medicine, 2024
2. Google Health, 2024
3. Science Robotics, 2023
4. Tesla, 2024
```

**Difference:** V2 provides clear source attribution for every claim ✅

---

## Testing Citation Preservation

To verify citations are preserved through synthesis:

```bash
# Run benchmark with documents (enables all agents)
python benchmark.py

# Check the output for:
# 1. Inline [Source, Year] citations in report text
# 2. Sources section with all citations
# 3. No orphaned citations
```

---

## Conclusion

The current implementation has a critical flaw: **citations are lost during synthesis**. The final reports lack inline source attribution, making it impossible for readers to verify claims.

The V2 agents fix this by:
1. Instructing the LLM to include inline citations
2. Actively extracting citations from findings
3. Preserving citations through synthesis
4. Creating properly attributed final reports

**Status:** Improved agents ready for deployment in `agents/*_v2.py`
