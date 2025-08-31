# 🚀 Local IT Support System Setup Guide

## 📋 Prerequisites

Before setting up the environment, you need:

1. **Jira Account** with admin access to create projects
2. **Gmail Account** (or other SMTP provider)
3. **Ollama** installed locally (for AI models)

## 🔧 Step-by-Step Setup

### 1. Create Environment File

```bash
# Copy the template
cp env.template .env

# Edit the .env file with your credentials
nano .env  # or use your preferred editor
```

### 2. Configure Jira Integration

#### Get Jira API Token:
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a name (e.g., "Jira Agent")
4. Copy the generated token

#### Update .env file:
```bash
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_USER=your-email@company.com
JIRA_TOKEN=your_api_token_here
JIRA_PROJECT_KEY=SCRUM
```

### 3. Configure SMTP (Email Notifications)

#### For Gmail:
1. Enable 2-Factor Authentication on your Google account
2. Go to [Google Account Security](https://myaccount.google.com/security)
3. Create an "App Password" for "Mail"
4. Use this password (not your regular password)

#### Update .env file:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
```

### 4. Configure AI Models

#### Option A: Ollama (Local - Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull required models (in another terminal)
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull mixtral:8x7b
```

#### Option B: OpenRouter (Cloud)
1. Get API key from [OpenRouter](https://openrouter.ai/keys)
2. Update .env:
```bash
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key_here
```

### 5. Test Configuration

```bash
# Start the server
python3 src/api/server.py

# Test with a request
curl -X POST "http://localhost:8002/request" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP001",
    "request_type": "software_access",
    "title": "Test Request",
    "description": "Testing system configuration",
    "priority": "medium",
    "urgency": "normal",
    "business_justification": "System testing",
    "desired_completion_date": "2024-01-15T00:00:00Z"
  }'
```

## 🔍 Verification Steps

### Check Jira Integration:
1. Look for new tickets in your Jira project
2. Check ticket status updates
3. Verify email notifications are sent

### Check AI Workflow:
1. Monitor server logs for AI agent execution
2. Verify decisions are being made (ALLOWED/DENIED/REQUIRES_APPROVAL)
3. Check that tickets are properly routed

## 🚨 Troubleshooting

### Common Issues:

1. **Jira Connection Failed:**
   - Verify JIRA_BASE_URL format
   - Check API token permissions
   - Ensure project key exists

2. **SMTP Authentication Failed:**
   - Use App Password, not regular password
   - Check 2FA is enabled
   - Verify port and TLS settings

3. **AI Models Not Working:**
   - Ensure Ollama is running (`ollama serve`)
   - Check model names match exactly
   - Verify network connectivity

4. **Port Already in Use:**
   - Change API_PORT in .env
   - Kill existing processes: `lsof -ti:8002 | xargs kill -9`

## 📞 Support

If you encounter issues:
1. Check server logs for error messages
2. Verify all environment variables are set
3. Ensure external services (Jira, SMTP) are accessible
4. Check that required models are downloaded (if using Ollama)

## 🎯 Next Steps

Once configured:
1. **Test the full workflow** with different request types
2. **Monitor Jira board** for ticket creation and updates
3. **Check email notifications** for approval requests
4. **Observe AI decision-making** in real-time
5. **Test human-in-the-loop** functionality

---

**🎉 Congratulations!** You now have a fully functional AI-powered IT support system with Jira integration!
