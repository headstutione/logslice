# logslice

Fast log file parser and filter utility with regex-based querying and output formatting.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git
cd logslice && pip install .
```

---

## Usage

```bash
# Filter lines matching a pattern
logslice parse app.log --match "ERROR|WARN"

# Filter by date range and format output as JSON
logslice parse app.log --match "ERROR" --after "2024-01-01" --before "2024-01-31" --format json

# Read from stdin
cat app.log | logslice parse --match "timeout"
```

**Python API:**

```python
from logslice import LogParser

parser = LogParser("app.log")
results = parser.query(pattern=r"ERROR\s+\w+", after="2024-01-01")

for entry in results:
    print(entry.timestamp, entry.message)
```

---

## Options

| Flag | Description |
|------|-------------|
| `--match` | Regex pattern to filter log lines |
| `--after` | Include lines after this timestamp |
| `--before` | Include lines before this timestamp |
| `--format` | Output format: `text`, `json`, `csv` |
| `--tail` | Show only the last N matching lines |

---

## License

MIT © 2024 yourname