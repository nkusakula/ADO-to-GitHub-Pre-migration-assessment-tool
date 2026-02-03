# ADO Migration Readiness Analyzer 🔍

A CLI tool + Web UI that analyzes Azure DevOps organizations and generates comprehensive migration readiness reports for GitHub migrations, with the ability to **migrate repositories**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Dashboard Screenshot](docs/dashboard.png)

## 🎯 Problem

Before migrating from Azure DevOps to GitHub, enterprises need to understand:
- What assets exist in their ADO organization
- Which items can migrate easily vs. require manual work
- How complex the migration will be
- What order to migrate things in

**GitHub Enterprise Importer (GEI) handles the migration, but no tool helps with planning.**

## ✨ Features

### CLI
- **📊 Organization Scan** - Discover all projects, repos, pipelines, and work items
- **🔍 Compatibility Analysis** - Identify what maps to GitHub and what doesn't
- **📈 Complexity Scoring** - Get Low/Medium/High ratings per asset type
- **📄 Rich Reports** - Console output, HTML, and JSON export

### Web UI (NEW!)
- **🎨 Beautiful Dashboard** - Visual summary with charts
- **⚙️ Configuration Wizard** - Easy setup for ADO and GitHub
- **📊 Interactive Reports** - Expandable project details
- **🚀 Repo Migration** - Select and migrate repos to GitHub with live progress

## 🚀 Quick Start

### Option 1: CLI Only

```bash
pip install -e .
ado-readiness configure
ado-readiness scan
ado-readiness report --format html -o report.html
```

### Option 2: Web UI

```bash
# Terminal 1: Start backend
cd backend
pip install -e . && pip install -e ../
uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser!

## 📖 Usage

### Configure your connection

```bash
ado-readiness configure
```

You'll be prompted for:
- Azure DevOps organization URL (e.g., `https://dev.azure.com/myorg`)
- Personal Access Token (PAT) with read permissions

### Test connection

```bash
ado-readiness test-connection
```

### Scan your organization

```bash
# Scan entire organization
ado-readiness scan

# Scan a specific project
ado-readiness scan --project MyProject

# Verbose output
ado-readiness scan --verbose
```

### Generate reports

```bash
# Console summary (default)
ado-readiness report

# Export to HTML
ado-readiness report --format html --output report.html

# Export to JSON
ado-readiness report --format json --output report.json
```

## 📊 Example Output

```
╭──────────────────────────────────────────────────────────╮
│           ADO Migration Readiness Report                 │
│           Organization: contoso-dev                      │
╰──────────────────────────────────────────────────────────╯

📊 Summary
┌─────────────┬───────┬────────────┬─────────────┐
│ Asset Type  │ Count │ Complexity │ Est. Effort │
├─────────────┼───────┼────────────┼─────────────┤
│ Repositories│    45 │ Low        │ 2 days      │
│ Pipelines   │   120 │ High       │ 2 weeks     │
│ Work Items  │ 3,400 │ Medium     │ 1 week      │
│ Boards      │    12 │ Low        │ 2 days      │
└─────────────┴───────┴────────────┴─────────────┘

Overall Migration Complexity: MEDIUM (65/100)

⚠️  Blockers Found: 3
  • 15 Classic pipelines require manual conversion
  • 5 custom work item types need mapping
  • 2 repos use TFVC (requires special handling)
```

## 🛠️ Development

```bash
# Clone the repo
git clone https://github.com/nkusakula/ADO-to-GitHub-Pre-migration-assessment-tool.git
cd ADO-to-GitHub-Pre-migration-assessment-tool

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

---

Built for the **GitHub Copilot CLI Hackathon** 🚀
