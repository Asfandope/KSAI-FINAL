# KS AI Platform

A bilingual (English/Tamil) AI-powered chat assistant providing credible, source-based information about Karthikeya Sivasenapathy (KS) and his work in Politics, Environmentalism, SKCRF, and Educational Trust.

## 🏗️ Architecture

This project uses a modern **monorepo architecture** with:

- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS, and Zustand
- **Backend**: FastAPI with Python 3.11, SQLAlchemy, and Pydantic
- **Database**: PostgreSQL for metadata, Qdrant for vector embeddings
- **AI/ML**: OpenAI GPT-3.5 and embeddings for RAG pipeline
- **Infrastructure**: Docker Compose for local development

## 🚀 Features

### Core Features ✅
- **Bilingual Support**: Full English and Tamil language support
- **RAG Pipeline**: Retrieval-Augmented Generation for grounded responses
- **User Authentication**: JWT-based authentication with email/phone
- **Chat Interface**: Real-time chat with conversation history
- **Admin Panel**: Content management and analytics dashboard
- **Content Ingestion**: PDF and YouTube video processing
- **Vector Search**: Semantic search using Qdrant vector database

### In Development 🚧
- **Voice Input/Output**: Speech-to-text and text-to-speech
- **Advanced Analytics**: Usage metrics and insights
- **Content Translation**: AI-powered Tamil translation
- **Mobile App**: React Native mobile application

## 📁 Project Structure

```
ks-ai-platform/
├── apps/
│   ├── web/                 # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/         # App router pages
│   │   │   ├── components/  # React components
│   │   │   └── lib/         # Utilities and state
│   │   └── package.json
│   └── api/                 # FastAPI backend
│       ├── app/
│       │   ├── routers/     # API routes
│       │   ├── services/    # Business logic
│       │   ├── models/      # Database models
│       │   └── core/        # Configuration
│       ├── alembic/         # Database migrations
│       └── requirements.txt
├── packages/
│   ├── ui/                  # Shared React components
│   ├── types/               # Shared TypeScript types
│   └── config/              # Shared configurations
├── scripts/
│   ├── dev.sh              # Development helper
│   └── migrate.sh          # Database migration helper
├── docker-compose.yml      # Local development stack
└── README.md
```

## 🛠️ Development Setup

### Prerequisites

- **Node.js** 18+ and **pnpm**
- **Python** 3.11+ and **pip**
- **Docker** and **Docker Compose**
- **OpenAI API Key** (for AI features)

### Quick Start

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd ks-ai-platform
   cp .env.example .env
   ```

2. **Add your API keys to `.env`**:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   # Add other API keys as needed
   ```

3. **Install dependencies**:
   ```bash
   ./scripts/dev.sh install
   ```

4. **Start development environment**:
   ```bash
   ./scripts/dev.sh start
   ```

5. **Access the application**:
   - **Frontend**: http://localhost:3000
   - **API Docs**: http://localhost:8000/docs
   - **Qdrant Dashboard**: http://localhost:6333/dashboard

### Manual Setup (Alternative)

If the helper script doesn't work, you can set up manually:

```bash
# Install Node.js dependencies
pnpm install

# Start Docker services
docker-compose up -d postgres redis qdrant

# Install Python dependencies
cd apps/api
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend (in one terminal)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd apps/web
pnpm dev
```

## 🗄️ Database Management

### Migrations

```bash
# Run migrations
./scripts/migrate.sh upgrade

# Create new migration
./scripts/migrate.sh generate "description of changes"

# View current status
./scripts/migrate.sh current

# Reset database (CAUTION: Destroys data)
./scripts/migrate.sh reset
```

### Default Admin Account

The system creates a default admin account:
- **Email**: admin@ksai.com  
- **Password**: admin123

**⚠️ Change this password in production!**

## 🤖 Using the System

### For End Users

1. **Visit the homepage** and select your language (English/Tamil)
2. **Choose a topic** (Politics, Environmentalism, SKCRF, Educational Trust)
3. **Start chatting** - ask questions and get source-based answers
4. **Register/Login** to save your conversation history

### For Administrators

1. **Login** with admin credentials at `/login`
2. **Access admin panel** - navigate to admin dashboard
3. **Upload content**:
   - Upload PDF documents
   - Add YouTube video URLs
   - Categorize and set language
   - Enable AI translation if needed
4. **Monitor processing** - view content ingestion status
5. **Analyze usage** - check user statistics and popular queries

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/ks_ai

# AI Services
OPENAI_API_KEY=your_openai_api_key

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# JWT Security
JWT_SECRET=your_super_secret_jwt_key

# Admin Account
ADMIN_EMAIL=admin@ksai.com
ADMIN_PASSWORD=change_this_password
```

### Frontend Configuration

In `apps/web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## 🚀 Deployment

### Frontend (Vercel)

1. **Connect repository** to Vercel
2. **Set environment variables**:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-api-domain.com
   ```
3. **Deploy** - Vercel will handle the build automatically

### Backend (AWS EC2)

1. **Setup EC2 instance** with Docker
2. **Clone repository** and configure environment
3. **Run with Docker**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```
4. **Setup reverse proxy** (nginx/cloudflare)

### Database (AWS RDS + Qdrant Cloud)

1. **Create RDS PostgreSQL** instance
2. **Update DATABASE_URL** in production environment
3. **Setup Qdrant Cloud** or self-hosted instance
4. **Update QDRANT_HOST/PORT** in production

## 📊 API Documentation

### Authentication Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

### Chat Endpoints

- `POST /chat` - Send chat message (authenticated)
- `GET /topics` - Get available topics

### Admin Endpoints

- `POST /admin/content` - Upload content (admin only)
- `GET /admin/content` - List all content (admin only)
- `GET /admin/dashboard` - Get dashboard stats (admin only)

### Example API Usage

```javascript
// Login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password123'
  })
});

// Send chat message
const chatResponse = await fetch('/api/chat', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: 'What are KS\'s environmental initiatives?',
    language: 'en',
    topic: 'Environmentalism'
  })
});
```

## 🧪 Testing

### Backend Tests
```bash
cd apps/api
pytest
```

### Frontend Tests
```bash
cd apps/web
pnpm test
```

### E2E Tests
```bash
pnpm test:e2e
```

## 🐛 Troubleshooting

### Common Issues

1. **Docker services not starting**:
   ```bash
   docker-compose down
   docker-compose up -d --force-recreate
   ```

2. **Database connection errors**:
   ```bash
   # Check if PostgreSQL is running
   docker-compose logs postgres
   
   # Reset database
   ./scripts/dev.sh reset-db
   ```

3. **Frontend build errors**:
   ```bash
   # Clear Next.js cache
   rm -rf apps/web/.next
   pnpm dev
   ```

4. **API key issues**:
   - Ensure `.env` file has correct API keys
   - Check API key permissions and quotas
   - Verify environment variable loading

### Debug Mode

Enable debug logging:
```bash
# Backend
export LOG_LEVEL=DEBUG

# Frontend  
export NEXT_PUBLIC_DEBUG=true
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Code Standards

- **TypeScript** for all frontend code
- **Python 3.11+** with type hints for backend
- **ESLint + Prettier** for code formatting
- **Conventional Commits** for commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:

- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs and feature requests
- **Development**: Use the helper scripts in `scripts/` directory

## 🙏 Acknowledgments

- **OpenAI** for GPT models and embeddings
- **Qdrant** for vector database technology
- **Vercel** for Next.js and deployment platform
- **FastAPI** for the excellent Python web framework

---

**Built with ❤️ for providing credible, source-based information about KS's important work.**