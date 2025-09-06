![Buddhi AI Logo](./public/logos/buddhi-ai-logo-64.png)

# Buddhi AI - Model Management System

A comprehensive AI model orchestration service with OpenAI-compatible API that allows you to search, download, manage, and run AI models from Hugging Face.

## 🚀 Features

### Model Management
- **Search Models**: Find AI models on Hugging Face by query, type, and language
- **Download & Cache**: Download models locally with progress tracking
- **Status Monitoring**: Real-time download progress and status updates
- **Model Listing**: View all downloaded models with metadata

### OpenAI-Compatible API
- **Chat Completions**: Compatible with OpenAI's chat completions API
- **Text Completions**: Compatible with OpenAI's completions API
- **Streaming Support**: Real-time streaming responses
- **Model Listing**: List available models in OpenAI format

### Authentication & Security
- JWT-based authentication with secure token management
- User registration and login system
- Protected endpoints requiring authentication

### Database Integration
- SQLAlchemy ORM with SQLite database
- Alembic migrations for schema management
- Model metadata persistence

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   Hugging Face  │
│  (Next.js)      │◄──►│   (FastAPI)      │◄──►│     Hub API     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Database       │
                       │   (SQLite)       │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Model Cache    │
                       │   (Local Files)  │
                       └──────────────────┘
```

## 📋 API Endpoints

### Model Management (`/models/`)
- `GET /models/search` - Search Hugging Face models
- `POST /models/download` - Download a model
- `GET /models/status` - Check download status
- `GET /models/` - List downloaded models
- `DELETE /models/{model_name}` - Delete a model

### OpenAI-Compatible (`/v1/`)
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions
- `POST /v1/completions` - Text completions
- Streaming support for both completion types

### Authentication (`/auth/`)
- `POST /auth/` - Register new user
- `POST /auth/token` - Login and get access token
- `POST /auth/logout` - Logout and blacklist token

## 🚦 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+ (for frontend)
- Git

### Backend Setup

1. **Clone and Navigate**
   ```bash
   git clone <repository>
   cd buddhi
   ```

2. **Python Environment Setup**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   # Create .env file
   echo "AUTH_SECRET_KEY=your-secret-key-here" > .env
   echo "AUTH_ALGORITHM=HS256" >> .env
   ```

5. **Database Setup**
   ```bash
   alembic upgrade head
   ```

6. **Start the Server**
   ```bash
   uvicorn backend.api.main:app --reload
   ```

### Frontend Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - API: http://localhost:8000

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_model_management.py -v
pytest tests/test_openai_api.py -v
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=backend tests/
```

## 📖 Documentation

- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI (when server is running)
- **[Database Schema](backend/models/base.py)** - SQLAlchemy models
- **[Testing Guide](TESTING.md)** - Testing procedures and guidelines

---

**Built with ❤️ by the Buddhi Kavindra**


To run the FastAPI backend app:

run the `runserver.bat` file on Windows:

```bash
.\runserver.bat
```

run the `runserver.sh` file on macOS/Linux:

```shell
./runserver.sh
```