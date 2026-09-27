# 🎙️ Shapir Recordings System

Speech-to-text and AI summarization platform for Shapir Engineering meetings.

## 📋 Overview

This system enables Shapir employees to:
1. Upload audio recordings (MP3, M4A, WAV, OGG)
2. Automatically transcribe them using OpenAI Whisper
3. Generate summaries using GPT-4
4. Export to various formats (PDF, DOCX, XLSX, TXT)
5. Maintain full data ownership on-premises

## 🏗️ Phase 1: Foundation (Current)

**Goal**: Core backend infrastructure + Whisper integration

### Components Completed
- ✅ FastAPI application setup
- ✅ Database models (SQLAlchemy)
- ✅ Configuration management
- ✅ Database connection layer
- ✅ Health check endpoint

### What's Next
- [ ] Authentication service (Windows AD/LDAP)
- [ ] File upload API endpoint
- [ ] Whisper integration service
- [ ] Transcript storage

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- SQL Server Express (or SQL Server)
- Windows Server with IIS (for production)
- OpenAI API key

### Installation

1. **Clone/Create project**
```bash
cd shapir-recordings
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your actual configuration
```

3. **Initialize database**
```bash
python -c "from database import init_db; init_db()"
```

4. **Run development server**
```bash
python main.py
# Or with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. **Access the API**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## 📁 Project Structure

```
shapir-recordings/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings (from environment)
├── models.py            # SQLAlchemy database models
├── database.py          # Database connection & initialization
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment configuration
├── .env                 # Your actual environment (NOT in git)
└── README.md            # This file

# Phase 2 & 3 will add:
├── services/
│   ├── auth.py         # AD/LDAP authentication
│   ├── whisper.py      # Whisper API integration
│   ├── gpt.py          # GPT summarization
│   ├── templates.py    # Template management
│   └── documents.py    # PDF/DOCX/XLSX generation
├── routes/
│   ├── auth.py         # Authentication endpoints
│   ├── recordings.py   # Recording CRUD endpoints
│   ├── templates.py    # Template endpoints
│   └── admin.py        # Admin dashboard endpoints
├── schemas/
│   └── *.py            # Pydantic request/response schemas
└── tests/
    └── *.py            # Unit & integration tests
```

---

## 🔐 Security

### API Keys
- **OpenAI API Key**: Store in `.env` (never commit)
- **Session Secret**: Generate a strong random string
- **Database Password**: Store securely in environment

### Database
- SQL Server on Windows Server (on-premises)
- Encrypted connections recommended
- Regular backups required

### Authentication
- Windows AD/LDAP integration
- No external login providers
- Session tokens (JWT-style)

---

## 📊 Database Schema

### Users
```sql
- id (UUID, primary key)
- email (unique)
- name
- ad_username
- ad_domain
- role (viewer|editor|admin)
- is_active
- created_at, last_login
```

### Recordings
```sql
- id (UUID, primary key)
- user_id (FK)
- file_name
- file_path
- file_size_mb
- file_format (mp3, m4a, wav, ogg)
- language (he, ar, en)
- transcription_status (pending|processing|completed|failed)
- duration_seconds
- created_at, transcribed_at, deleted_at
```

### Transcripts
```sql
- id (UUID, primary key)
- recording_id (FK, unique)
- text
- language
- api_cost (USD)
- processing_time_seconds
- created_at
```

### Templates
```sql
- id (UUID, primary key)
- name (unique)
- description
- system_prompt
- user_prompt_template
- output_format (txt|pdf|docx|xlsx)
- is_active
- created_at, updated_at
```

### Summaries
```sql
- id (UUID, primary key)
- recording_id (FK)
- template_id (FK)
- summary_text
- api_cost (USD)
- processing_time_seconds
- model_used
- created_at
```

### AuditLog
```sql
- id (UUID, primary key)
- user_id (FK)
- action (upload|transcribe|summarize|download|delete)
- resource_type
- resource_id
- ip_address
- created_at
```

---

## 🔌 API Endpoints (Phase 1)

### Health & Status
```
GET  /health                 - Health check
GET  /                       - API root info
```

### Phase 2 (Authentication)
```
POST /api/auth/login         - AD login
GET  /api/auth/user          - Current user
POST /api/auth/logout        - Logout
```

### Phase 2 (Recordings & Transcription)
```
POST /api/recordings/upload  - Upload audio file
GET  /api/recordings         - List user's recordings
GET  /api/recordings/{id}    - Get recording details
GET  /api/recordings/{id}/transcript - Get transcript
DELETE /api/recordings/{id}  - Delete recording
```

### Phase 3 (Summarization)
```
POST /api/summaries          - Create summary
GET  /api/summaries/{id}     - Get summary
GET  /api/summaries?recording_id=X - List summaries
```

### Phase 3 (Templates)
```
GET  /api/templates          - List all templates
POST /api/templates          - Create template (admin)
PUT  /api/templates/{id}     - Update template (admin)
DELETE /api/templates/{id}   - Delete template (admin)
```

### Phase 4 (Admin)
```
GET  /api/admin/users        - List users
GET  /api/admin/usage        - Usage statistics
GET  /api/admin/logs         - Audit logs
```

---

## 📝 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEBUG` | No | False | Enable debug mode |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `DATABASE_URL` | Yes | - | SQL Server connection string |
| `AD_SERVER` | Yes | ldap://localhost:389 | LDAP server URL |
| `AD_BASE_DN` | Yes | dc=shapir,dc=local | LDAP base DN |
| `UPLOAD_DIR` | No | ./uploads | File upload directory |
| `MAX_FILE_SIZE_MB` | No | 100 | Max file size |
| `RETENTION_DAYS` | No | 30 | Days to retain recordings |
| `LOG_LEVEL` | No | INFO | Logging level |

---

## 🧪 Testing

```bash
# Run health check
curl http://localhost:8000/health

# View API documentation
# Visit http://localhost:8000/docs in browser
```

---

## 📈 Cost Estimation

### OpenAI API Costs
- **Whisper**: $0.02 per minute of audio
- **GPT-4**: $0.03 per 1K input tokens, $0.06 per 1K output tokens

### Example (1 hour meeting)
- Transcription (60 min × $0.02): $1.20
- Summary (GPT-4): ~$0.30
- **Total per meeting**: ~$1.50

### For 50-200 users (100 recordings/month)
- **Monthly cost**: ~$150 (conservative estimate)
- **Existing budget**: Likely covers this

---

## 🔄 Deployment (Phase 4)

### Windows Server Setup
```powershell
# Install Python 3.11+
choco install python

# Install SQL Server Express
# (or use existing instance)

# Clone repository
git clone https://github.com/shapir/recordings.git

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with actual values

# Initialize database
python -c "from database import init_db; init_db()"

# Install as Windows Service (using NSSM)
nssm install ShapirRecordings "C:\path\to\venv\Scripts\python.exe main.py"
```

### IIS Configuration
```xml
<!-- web.config for IIS -->
<configuration>
  <system.webServer>
    <handlers>
      <add name="FastAPI" path="*" verb="*" 
           modules="FastCgiModule" 
           scriptProcessor="[PATH]\python.exe|[PATH]\main.py" />
    </handlers>
  </system.webServer>
</configuration>
```

---

## 📞 Support & Troubleshooting

### Database Connection Issues
```
Error: "Connection to SQL Server failed"
Solution: 
1. Verify DATABASE_URL format
2. Check SQL Server is running
3. Verify credentials and network connectivity
```

### OpenAI API Errors
```
Error: "Invalid API key"
Solution:
1. Verify OPENAI_API_KEY in .env
2. Check key is valid in OpenAI dashboard
3. Ensure sufficient API quota
```

### AD Authentication Issues
```
Error: "Failed to bind to LDAP server"
Solution:
1. Verify AD_SERVER URL
2. Check service account credentials (if used)
3. Verify network/firewall access to LDAP port 389
```

---

## 📜 License

Internal Shapir Engineering tool - All rights reserved

---

## 🗓️ Timeline

- **Phase 1** (Week 1-2): Foundation ✅
- **Phase 2** (Week 3-4): Frontend & Auth
- **Phase 3** (Week 5-6): GPT & Templates
- **Phase 4** (Week 7-8): Deployment & Testing

---

## 👥 Team

- **Project Owner**: Finance Department (Shapir Engineering)
- **Development**: Claude Code
- **Architecture**: FastAPI + React + SQL Server

---

**Last Updated**: September 2026

**Next Phase**: Phase 2 - Authentication & Frontend
