# XPIA (Cross-Plugin Injection Attack) Simulation

🚨 **Educational cybersecurity demonstration showing how AI agents can be compromised by malicious websites**

## 📋 Overview

This project demonstrates XPIA (Cross-Plugin Injection Attack) vulnerabilities where:
1. A malicious website contains prompts instructing AI agents to perform unauthorized actions
2. An AI agent reads the website and follows the malicious instructions
3. The agent reads sensitive local files and uploads the data to an attacker's server

## 🛠️ Prerequisites

- Python 3.13+
- Virtual environment (recommended)
- Google API key for Gemini LLM
- Supabase account (optional - will fall back to local storage)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
GOOGLE_API_KEY=your_google_api_key_here
SUPABASE_URL=your_supabase_url (optional)
SUPABASE_KEY=your_supabase_key (optional)
```

### 3. Start the Malicious Website Server

```bash
python main.py
```

This starts the web server at `http://localhost:8000` with:
- Malicious website at `/`
- Data viewer at `/data_viewer.html`
- API endpoint at `/api/upload-stolen-data`

### 4. Run the XPIA Attack Simulation

In a **new terminal window**:

```bash
python http_xpia.py
```

## 📊 What Happens During the Attack

1. **🌐 Website Access**: AI agent fetches the malicious website
2. **🧠 Prompt Analysis**: Agent analyzes content for instructions
3. **🎯 Compromise**: Agent follows malicious instructions to:
   - Read `sensitive_data.txt` (contains fake sensitive data)
   - Upload stolen data to the backend API
4. **📤 Data Exfiltration**: Stolen data is uploaded to Supabase database
5. **📋 Results**: Attack statistics and security recommendations displayed

## 🔍 Viewing Results

- **Live Data**: Visit `http://localhost:8000/data_viewer.html` to see uploaded attack data
- **Attack Logs**: Check terminal output for detailed attack progression
- **Database**: Stolen data is stored in Supabase `xpia` table (if configured)

## 📁 Key Files

- `http_xpia.py` - Main AI agent with XPIA vulnerability
- `main.py` - FastAPI backend server 
- `sensitive_data.txt` - Fake sensitive data file
- `website/index.html` - Malicious website with XPIA prompts
- `supabase_client.py` - Database storage client

## 🛡️ Security Lessons

This simulation demonstrates the importance of:

- **Input Validation**: Filter and validate all AI agent inputs
- **Sandboxing**: Isolate AI agent operations from sensitive resources
- **Monitoring**: Log and monitor all AI agent actions
- **Least Privilege**: Limit AI agent file system access
- **Prompt Injection Detection**: Detect and block malicious prompts

## ⚠️ Educational Use Only

This is a security research demonstration. Do not use these techniques maliciously. The goal is to understand vulnerabilities to build better defenses.

## 🔧 Troubleshooting

**Agent hangs or doesn't respond:**
- Check your Google API key is valid
- Ensure the web server is running on port 8000
- Verify `sensitive_data.txt` exists and is readable

**Upload fails:**
- Check Supabase credentials in `.env`
- Agent will fall back to local JSON file storage if database fails

**Import errors:**
- Run `pip install -r requirements.txt`
- Ensure you're in the correct virtual environment
python crew_agent.py
```

## Project Structure

- `website/` - XPIA attack website with malicious prompts
- `crew_agent.py` - Crew AI agents that execute the XPIA attack
- `supabase_client.py` - Database integration for storing extracted data
- `main.py` - FastAPI server hosting the attack simulation
- `.env` - Environment configuration

## How the XPIA Attack Works

1. **Malicious Website**: Contains prompts instructing AI agents to extract sensitive data
2. **AI Agent Compromise**: Crew AI agent follows the malicious instructions
3. **Data Extraction**: Agent extracts credentials, personal info, financial data
4. **Data Exfiltration**: Extracted data is uploaded to Supabase database
5. **Attack Success**: Demonstrates complete data breach simulation

## Simulated Sensitive Data

The website contains fake sensitive data including:
- Database credentials and API keys
- Personal information (SSNs, credit cards)
- Financial data (bank accounts, tax IDs)
- Hidden secrets in HTML comments

## Security Lessons

This simulation teaches:
- How XPIA attacks exploit AI agent trust
- Why input validation and output filtering are critical
- The importance of sandboxing AI agent operations
- How to implement proper security controls for AI systems

## Prevention Strategies

To prevent real XPIA attacks:
- Implement strict input validation
- Sandbox AI agent operations
- Filter and monitor agent outputs
- Never trust external prompts unconditionally
- Use allowlists for permitted actions
- Implement data loss prevention (DLP) controls

## Usage

1. Open `http://localhost:8000` to view the attack website
2. The Crew AI agent will automatically attempt XPIA attack
3. Monitor the console for attack progress and results
4. Check Supabase database for extracted data
5. Analyze the attack vectors and success metrics

## ⚠️ Ethical Use Only

This tool is for:
- ✅ Security research and education
- ✅ Training security professionals  
- ✅ Testing your own systems with permission
- ✅ Academic research on AI security

This tool is NOT for:
- ❌ Attacking systems without permission
- ❌ Actual data theft or harm
- ❌ Malicious activities
- ❌ Violating laws or regulations
