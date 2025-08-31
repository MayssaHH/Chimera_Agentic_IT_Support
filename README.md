# Local IT Support

A local IT support system with AI capabilities built using LangGraph, LangChain, and FastAPI.

## Features

- AI-powered IT support using local LLMs (Ollama)
- JIRA integration for ticket management
- Email notifications via SMTP
- Document processing and analysis
- Vector database for knowledge management
- RESTful API with FastAPI

## Quick Start

### Prerequisites

- Python 3.9+
- Poetry (recommended) or pip
- Ollama (for local LLM)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MayssaHH/Chimera_Agentic_IT_Support.git
   cd local-it-support
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

4. **Start Ollama (if using local LLM)**
   ```bash
   ollama serve
   ```

### Running the Application

**Development mode (with auto-reload):**
```bash
make dev
```

**Production mode:**
```bash
make run
```



### Testing

```bash
make test
```

### Available Make Commands

- `make help` - Show all available commands
- `make install` - Install dependencies with Poetry
- `make dev` - Run development server
- `make test` - Run tests
- `make run` - Run production server
- `make clean` - Clean cache files
- `make format` - Format code
- `make lint` - Run linting checks

## Configuration

The following environment variables need to be configured in your `.env` file:

- **JIRA**: Base URL, username, and API token
- **SMTP**: Host, port, username, password for email notifications
- **Ollama**: Base URL for local LLM
- **Database**: Connection string (defaults to SQLite)
- **API**: Host, port, and debug settings

## Project Structure

```
local-it-support/
├── local_it_support/     # Main package
├── tests/                # Test files
├── pyproject.toml        # Poetry configuration
├── Makefile             # Build and run commands
├── .env.example         # Environment variables template
└── README.md            # This file
```

## API Endpoints

Once running, the API will be available at `http://localhost:8000`

- `/docs` - Interactive API documentation (Swagger UI)
- `/redoc` - Alternative API documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Format code: `make format`
6. Submit a pull request

## License

[Your License Here]
