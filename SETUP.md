# Setup Guide

## Prerequisites

- Python 3.8 or higher
- An OpenAI API key from [platform.openai.com](https://platform.openai.com)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

#### Option A: Using .env file (Recommended)

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your favorite editor and add your API key:
# OPENAI_API_KEY=sk-your-actual-key-here
```

#### Option B: Export as environment variable

```bash
export OPENAI_API_KEY="sk-your-actual-key-here"
```

#### Option C: Set in system environment (Windows)

```powershell
$env:OPENAI_API_KEY="sk-your-actual-key-here"
```

### 3. Verify Installation

```bash
# Test the installation
python -c "from openai import OpenAI; print('✓ OpenAI library installed')"
python -c "import dotenv; print('✓ python-dotenv installed')"
```

## Usage

### Command Line

```bash
# Basic research
python main.py "What is quantum computing?"

# With focus areas
python main.py "Machine learning advances" \
  --focus-areas "Deep Learning" "Large Language Models"

# Academic tone
python main.py "Climate change solutions" \
  --tone academic \
  --max-sources 10

# JSON output
python main.py "AI trends" --output-format json
```

### Python Code

```python
import asyncio
from coordinator import ResearchCoordinator

async def research():
    coordinator = ResearchCoordinator()
    report = await coordinator.research(
        topic="Your research topic",
        focus_areas=["Area 1", "Area 2"],
        tone="academic",
    )
    print(report.to_markdown())

asyncio.run(research())
```

## Troubleshooting

### "No module named 'openai'"
```bash
pip install --upgrade openai
```

### "No module named 'dotenv'"
```bash
pip install python-dotenv
```

### "OPENAI_API_KEY not found"

1. Check that .env file exists in the project root
2. Verify the file contains: `OPENAI_API_KEY=sk-...`
3. Make sure you're running from the project directory
4. Try exporting the variable manually:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

### API Rate Limits

If you hit OpenAI rate limits:
- Wait a few minutes before trying again
- Consider using `gpt-3.5-turbo` for cheaper/faster requests
- Reduce `max_sources` parameter

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `DEBUG` | No | false | Enable debug logging |

## Getting an OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Navigate to API keys: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the key and add to .env file

## Next Steps

- See [README.md](README.md) for full documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- Run `examples.py` for usage examples
- Run tests: `pytest tests/ -v`
