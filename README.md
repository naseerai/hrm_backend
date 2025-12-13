# HRM 

A FastAPI project using uv for dependency management.

## 🚀 Quick Start

### Prerequisites
- Python >=3.12

### Installation & Setup

1. **Install uv** (Python's fastest package manager)

pip install uv


2. **Create virtual environment**

uv venv

*Creates `.venv` in your project root*

3. **Install all dependencies** (from `pyproject.toml` + `uv.lock`)

uv sync --production


*Installs production + dev dependencies with exact versions*

4. **Run the application**

uvicorn main:app --host 0.0.0.0 --port 8001 --reload

*Access at `http://localhost:8001` | `--reload` for development*
