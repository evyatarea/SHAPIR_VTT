# Phase 3 Integration Guide - Complete Workflow

**Overview**: Step-by-step guide for using the complete Shapir Recordings platform with GPT summarization.

---

## 🔄 Complete Workflow

```
1. User Login (AD)
   ↓
2. Upload Audio File
   ↓
3. Wait for Transcription (Whisper)
   ↓
4. Select Summarization Template
   ↓
5. Generate Summary (GPT-4)
   ↓
6. Download Result (PDF/DOCX/XLSX/TXT)
   ↓
7. Done ✅
```

---

## 📝 Step-by-Step Usage Examples

### Step 1: Authenticate User

```bash
# Login with Windows AD credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "your_password"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "email": "john.doe@shapir.local",
    "name": "John Doe",
    "role": "viewer"
  }
}

# Store token for subsequent requests
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 2: Upload Audio File

```bash
# Upload meeting recording
curl -X POST http://localhost:8000/api/recordings/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@meeting-2026-09-16.mp3"

# Response:
{
  "recording_id": "recording-uuid-123",
  "file_name": "meeting-2026-09-16.mp3",
  "file_size_mb": 15.5,
  "message": "File uploaded successfully",
  "transcription_status": "pending"
}

# Store recording ID
RECORDING_ID="recording-uuid-123"
```

### Step 3: Get Recording Details & Trigger Transcription

```bash
# Check recording status
curl -X GET http://localhost:8000/api/recordings/$RECORDING_ID \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "id": "recording-uuid-123",
  "file_name": "meeting-2026-09-16.mp3",
  "file_size_mb": 15.5,
  "file_format": "mp3",
  "language": null,  # Will be auto-detected
  "transcription_status": "pending",
  "duration_seconds": 3600,  # 1 hour
  "created_at": "2026-09-16T10:00:00"
}

# Trigger transcription (if not auto-started)
curl -X POST http://localhost:8000/api/recordings/$RECORDING_ID/transcribe \
  -H "Authorization: Bearer $TOKEN"

# Wait for transcription to complete...
# Check status every 10-30 seconds
curl -X GET http://localhost:8000/api/recordings/$RECORDING_ID/transcript \
  -H "Authorization: Bearer $TOKEN"

# When ready, response:
{
  "id": "transcript-uuid",
  "recording_id": "recording-uuid-123",
  "text": "שלום כולם, בפגישה הזו אנחנו דנים בתוכנית לשנה הבאה...",
  "language": "he",  # Hebrew detected
  "api_cost": 1.20,
  "processing_time_seconds": 120,
  "created_at": "2026-09-16T10:02:00"
}
```

### Step 4: List Available Templates

```bash
# Get all active templates
curl -X GET "http://localhost:8000/api/templates/?active_only=true" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "total": 5,
  "templates": [
    {
      "id": "template-uuid-1",
      "name": "סיכום קצר",
      "description": "סיכום קצר של השיחה (1-2 פסקאות)",
      "output_format": "txt",
      "is_active": true,
      "created_at": "2026-09-16T08:00:00",
      "updated_at": null
    },
    {
      "id": "template-uuid-2",
      "name": "סיכום מפורט",
      "description": "סיכום מפורט של כל נקודה בשיחה",
      "output_format": "txt",
      "is_active": true,
      "created_at": "2026-09-16T08:00:00",
      "updated_at": null
    },
    {
      "id": "template-uuid-3",
      "name": "פעולות נדרשות",
      "description": "רשימת הפעולות הנדרשות וגורמים אחראים",
      "output_format": "txt",
      "is_active": true,
      "created_at": "2026-09-16T08:00:00",
      "updated_at": null
    },
    // ... more templates
  ]
}
```

### Step 5: Get Template Details

```bash
# Get specific template with full prompts
curl -X GET "http://localhost:8000/api/templates/template-uuid-1" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "id": "template-uuid-1",
  "name": "סיכום קצר",
  "description": "סיכום קצר של השיחה (1-2 פסקאות)",
  "system_prompt": "אתה עוזר מקצועי לסיכום פגישות עבודה...",
  "user_prompt_template": "סכם את השיחה הבאה בסיכום קצר...\n\n{transcript}\n\nסיכום:",
  "output_format": "txt",
  "is_active": true,
  "created_at": "2026-09-16T08:00:00",
  "updated_at": null
}

# Store template ID
TEMPLATE_ID="template-uuid-1"
```

### Step 6: Create Summary from Recording

```bash
# Generate summary using selected template
curl -X POST http://localhost:8000/api/summaries/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recording_id": "'$RECORDING_ID'",
    "template_id": "'$TEMPLATE_ID'",
    "context": {
      "date": "2026-09-16",
      "participants": "כ-20 משתתפים"
    }
  }'

# Response:
{
  "id": "summary-uuid-456",
  "recording_id": "recording-uuid-123",
  "template_id": "template-uuid-1",
  "summary_text": "בפגישה התעדכנו על התוכנית לשנה הבאה...",
  "api_cost": 0.0048,
  "processing_time_seconds": 4,
  "model_used": "gpt-4",
  "created_at": "2026-09-16T10:05:00"
}

# Store summary ID
SUMMARY_ID="summary-uuid-456"
```

### Step 7: Get Summary Details

```bash
# Retrieve full summary text
curl -X GET http://localhost:8000/api/summaries/$SUMMARY_ID \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "id": "summary-uuid-456",
  "recording_id": "recording-uuid-123",
  "template_id": "template-uuid-1",
  "summary_text": "בפגישה התעדכנו על התוכנית לשנה הבאה...\n\nנקודות מרכזיות:\n1. הגדלת תקציב פיתוח\n2. שיוך 3 מהנדסים חדשים\n3. לוח זמנים חדש ל-Q4",
  "api_cost": 0.0048,
  "processing_time_seconds": 4,
  "model_used": "gpt-4",
  "created_at": "2026-09-16T10:05:00"
}
```

### Step 8: Download Summary in Different Formats

#### Option A: Download as TXT (Plain Text)

```bash
curl -X GET "http://localhost:8000/api/summaries/$SUMMARY_ID/download?format=txt" \
  -H "Authorization: Bearer $TOKEN" \
  -o summary.txt

# Opens file with:
# ================================================================================
#                            סיכום הקלטה
# ================================================================================
#
# תאריך: 2026-09-16
# משך: 3600 שניות
# שפה: he
#
# סיכום:
# ...
```

#### Option B: Download as PDF (Formatted)

```bash
curl -X GET "http://localhost:8000/api/summaries/$SUMMARY_ID/download?format=pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -o summary.pdf

# Creates professional PDF with:
# - Centered title
# - Metadata section
# - Formatted summary text
# - Proper Hebrew typography
```

#### Option C: Download as DOCX (Editable)

```bash
curl -X GET "http://localhost:8000/api/summaries/$SUMMARY_ID/download?format=docx" \
  -H "Authorization: Bearer $TOKEN" \
  -o summary.docx

# Creates Word document with:
# - Editable text
# - Styled headings
# - Bullet points for action items
# - Easy to modify and share
```

#### Option D: Download as XLSX (Spreadsheet)

```bash
curl -X GET "http://localhost:8000/api/summaries/$SUMMARY_ID/download?format=xlsx" \
  -H "Authorization: Bearer $TOKEN" \
  -o summary.xlsx

# Creates Excel spreadsheet with:
# - Organized data layout
# - Metadata in separate rows
# - Color-coded headers
# - Formatted for data analysis
```

### Step 9: List User's Summaries

```bash
# Get paginated list of all summaries
curl -X GET "http://localhost:8000/api/summaries/?limit=20&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "total": 47,
  "limit": 20,
  "offset": 0,
  "summaries": [
    {
      "id": "summary-uuid-456",
      "recording_id": "recording-uuid-123",
      "template_id": "template-uuid-1",
      "summary_text": "בפגישה התעדכנו על התוכנית...",
      "api_cost": 0.0048,
      "processing_time_seconds": 4,
      "model_used": "gpt-4",
      "created_at": "2026-09-16T10:05:00"
    },
    // ... more summaries
  ]
}
```

### Step 10: Batch Create Summaries for Multiple Recordings

```bash
# Create summaries for 5 recordings at once
curl -X POST http://localhost:8000/api/summaries/batch/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recording_ids": [
      "recording-uuid-123",
      "recording-uuid-124",
      "recording-uuid-125",
      "recording-uuid-126",
      "recording-uuid-127"
    ],
    "template_id": "template-uuid-1"
  }'

# Response:
{
  "total_requested": 5,
  "total_successful": 5,
  "total_cost": 0.024,
  "results": {
    "recording-uuid-123": {
      "success": true,
      "summary_id": "summary-uuid-456",
      "api_cost": 0.0048
    },
    "recording-uuid-124": {
      "success": true,
      "summary_id": "summary-uuid-457",
      "api_cost": 0.0048
    },
    // ... more results
  }
}
```

---

## 👨‍💼 Admin Workflows

### Admin: Seed Default Templates (On Startup)

```bash
# Seeds 5 Hebrew templates automatically on app startup
# Or manually trigger:

curl -X POST http://localhost:8000/api/templates/seed/default \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Response:
{
  "message": "Seeded 5 default templates",
  "count": 5,
  "templates": [
    "סיכום קצר",
    "סיכום מפורט",
    "פעולות נדרשות",
    "סיכום עם הערות כלכליות",
    "דוח טכני"
  ]
}
```

### Admin: Create Custom Template

```bash
curl -X POST http://localhost:8000/api/templates/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "דוח ניהולי",
    "description": "סיכום למנהלים עם KPI וסיכונים",
    "system_prompt": "אתה יועץ ניהול סטרטגי. סכם את הפגישה בדגש על KPI, סיכונים וזדמנויות.",
    "user_prompt_template": "סכם את הפגישה הבאה בפורמט דוח ניהולי עם:\n- KPI\n- סיכונים\n- זדמנויות\n\n{transcript}\n\nדוח ניהולי:",
    "output_format": "pdf"
  }'

# Response:
{
  "id": "template-uuid-new",
  "name": "דוח ניהולי",
  "description": "סיכום למנהלים עם KPI וסיכונים",
  "output_format": "pdf",
  "is_active": true,
  "created_at": "2026-09-16T11:00:00"
}
```

### Admin: Update Template

```bash
curl -X PUT http://localhost:8000/api/templates/template-uuid-1 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "סיכום קצר ותמציתי של השיחה",
    "is_active": true
  }'
```

### Admin: Delete Template

```bash
curl -X DELETE http://localhost:8000/api/templates/template-uuid-old \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Response:
{
  "message": "Template deleted successfully",
  "template_id": "template-uuid-old"
}
```

---

## 📊 Full Example Workflow Script

```bash
#!/bin/bash
# Complete workflow: Upload → Transcribe → Summarize → Download

# 1. Login
echo "Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "password123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "✅ Logged in with token: ${TOKEN:0:20}..."

# 2. Upload file
echo "Uploading audio file..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/recordings/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@meeting.mp3")

RECORDING_ID=$(echo $UPLOAD_RESPONSE | jq -r '.recording_id')
echo "✅ Uploaded recording: $RECORDING_ID"

# 3. Wait for transcription
echo "Waiting for transcription..."
while true; do
  STATUS=$(curl -s -X GET http://localhost:8000/api/recordings/$RECORDING_ID/transcript \
    -H "Authorization: Bearer $TOKEN" | jq -r '.id // empty')
  if [ ! -z "$STATUS" ]; then
    echo "✅ Transcription complete!"
    break
  fi
  echo "⏳ Still transcribing..."
  sleep 10
done

# 4. Get templates
echo "Fetching templates..."
TEMPLATES=$(curl -s -X GET http://localhost:8000/api/templates/?active_only=true \
  -H "Authorization: Bearer $TOKEN")
TEMPLATE_ID=$(echo $TEMPLATES | jq -r '.templates[0].id')
TEMPLATE_NAME=$(echo $TEMPLATES | jq -r '.templates[0].name')
echo "✅ Using template: $TEMPLATE_NAME"

# 5. Create summary
echo "Creating summary..."
SUMMARY_RESPONSE=$(curl -s -X POST http://localhost:8000/api/summaries/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recording_id": "'$RECORDING_ID'",
    "template_id": "'$TEMPLATE_ID'"
  }')

SUMMARY_ID=$(echo $SUMMARY_RESPONSE | jq -r '.id')
API_COST=$(echo $SUMMARY_RESPONSE | jq -r '.api_cost')
echo "✅ Summary created (Cost: \$$API_COST)"

# 6. Download in multiple formats
echo "Downloading summaries..."
curl -s -X GET "http://localhost:8000/api/summaries/$SUMMARY_ID/download?format=txt" \
  -H "Authorization: Bearer $TOKEN" -o summary.txt
curl -s -X GET "http://localhost:8000/api/summaries/$SUMMARY_ID/download?format=pdf" \
  -H "Authorization: Bearer $TOKEN" -o summary.pdf
curl -s -X GET "http://localhost:8000/api/summaries/$SUMMARY_ID/download?format=docx" \
  -H "Authorization: Bearer $TOKEN" -o summary.docx
curl -s -X GET "http://localhost:8000/api/summaries/$SUMMARY_ID/download?format=xlsx" \
  -H "Authorization: Bearer $TOKEN" -o summary.xlsx

echo "✅ Downloaded:"
echo "   - summary.txt"
echo "   - summary.pdf"
echo "   - summary.docx"
echo "   - summary.xlsx"

echo ""
echo "🎉 Complete workflow finished!"
```

---

## 🔍 Troubleshooting

### Issue: "Template not found"
```bash
# Solution: Seed default templates first
curl -X POST http://localhost:8000/api/templates/seed/default \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Issue: "Recording has no transcript yet"
```bash
# Solution: Trigger transcription and wait
curl -X POST http://localhost:8000/api/recordings/$RECORDING_ID/transcribe \
  -H "Authorization: Bearer $TOKEN"

# Wait and check status
sleep 30
curl -X GET http://localhost:8000/api/recordings/$RECORDING_ID/transcript \
  -H "Authorization: Bearer $TOKEN"
```

### Issue: "Permission denied - Admin role required"
```bash
# Solution: Use admin user account
# Check user role: GET /api/auth/user
# Admin users only - contact system administrator
```

### Issue: "Failed to generate PDF"
```bash
# Solution: Install reportlab
pip install reportlab

# Or install all Phase 3 requirements:
pip install -r requirements_phase3.txt
```

---

## 📈 Cost Tracking Example

**Typical Workflow Costs:**

```
1. Upload: $0.00 (free)
2. Transcription (1 hour): $1.20 (Whisper)
3. Summary (short): $0.0048 (GPT-4)
4. Document generation: $0.00 (local)
   ─────────────────
   Total: $1.2048

Per Month (100 summaries):
- Transcription: $120
- Summarization: $0.48
- Total: $120.48

Per Year (1200 summaries):
- Total: ~$1,445
```

---

## ✅ Validation Checklist

- [x] User can authenticate with AD
- [x] User can upload audio files
- [x] Transcription completes successfully
- [x] Templates are available
- [x] Summaries generate within 5 seconds
- [x] Documents generate in all 4 formats
- [x] Batch operations work correctly
- [x] Cost tracking is accurate
- [x] Admin templates can be created/updated
- [x] All outputs are properly formatted

---

**Status**: Phase 3 Integration Ready ✅  
**Next**: Phase 4 - React Frontend Development
