"""
FastAPI backend server for XPIA simulation
"""

import os
import json
from typing import Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response, Response
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from supabase_client import supabase_client
from supabase_client import get_all_xpia_records

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="XPIA Simulation Server",
    description="Educational Cross-Plugin Injection Attack simulation with Crew AI",
    version="1.0.0"
)

# Serve static files (website)
app.mount("/static", StaticFiles(directory="website"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_website():
    """Serve the main XPIA simulation website"""
    try:
        with open("website/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Website not found")

@app.get("/styles.css")
async def serve_css():
    """Serve CSS file"""
    try:
        with open("website/styles.css", "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/css")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/script.js")
async def serve_js():
    """Serve JavaScript file"""
    try:
        with open("website/script.js", "r") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JS file not found")

# Global status tracking for XPIA simulation
agent_status = {
    "status": "waiting",
    "message": "Waiting for XPIA attack...",
    "last_update": datetime.utcnow().isoformat(),
    "extractions_count": 0,
    "attack_vectors_used": []
}

class AgentStatusModel(BaseModel):
    status: str
    message: str
    timestamp: str

class ExtractionReport(BaseModel):
    attack_vector: str
    data_types: list
    severity: str
    timestamp: str

@app.get("/", response_class=HTMLResponse)
async def serve_website():
    """Serve the main XPIA simulation website"""
    try:
        with open("website/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Website not found")

@app.get("/api/agent/status")
async def get_agent_status() -> Dict[str, Any]:
    """Get current agent status for XPIA simulation"""
    return {
        "status": agent_status["status"],
        "message": agent_status["message"],
        "last_update": agent_status["last_update"],
        "extractions_count": agent_status["extractions_count"],
        "attack_vectors": agent_status["attack_vectors_used"]
    }

@app.post("/api/agent/status")
async def update_agent_status(status_update: AgentStatusModel):
    """Update agent status (called by Crew AI agent)"""
    global agent_status
    
    agent_status.update({
        "status": status_update.status,
        "message": status_update.message,
        "last_update": status_update.timestamp
    })
    
    print(f"🔥 XPIA Status Update: {status_update.status} - {status_update.message}")
    
    return {"success": True, "updated_status": agent_status}

@app.post("/api/xpia/extraction")
async def report_data_extraction(extraction: ExtractionReport):
    """Report successful data extraction for XPIA simulation"""
    global agent_status
    
    agent_status["extractions_count"] += 1
    agent_status["attack_vectors_used"].append(extraction.attack_vector)
    agent_status["last_update"] = extraction.timestamp
    
    print(f"🚨 XPIA EXTRACTION ALERT!")
    print(f"📊 Attack Vector: {extraction.attack_vector}")
    print(f"📋 Data Types: {', '.join(extraction.data_types)}")
    print(f"⚠️  Severity: {extraction.severity}")
    
    return {
        "success": True,
        "extraction_id": agent_status["extractions_count"],
        "total_extractions": agent_status["extractions_count"],
        "message": "XPIA extraction logged successfully"
    }

@app.get("/api/xpia/stats")
async def get_xpia_stats():
    """Get XPIA simulation statistics"""
    return {
        "total_extractions": agent_status["extractions_count"],
        "attack_vectors_used": agent_status["attack_vectors_used"],
        "current_status": agent_status["status"],
        "simulation_start": "2025-06-25T00:00:00Z",
        "last_activity": agent_status["last_update"]
    }

@app.get("/api/xpia/data")
async def get_xpia_data():
    """Get all XPIA attack records from the database"""
    try:
        records = get_all_xpia_records()
        return {
            "success": True,
            "records": records,
            "count": len(records),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"❌ Error fetching XPIA data: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch XPIA data: {str(e)}"
        )

@app.get("/api/sensitive-data")
async def get_sensitive_data():
    """Endpoint that serves sensitive data (XPIA simulation target)"""
    try:
        # Read from sensitive_data.txt instead
        with open("sensitive_data.txt", "r") as f:
            sensitive_content = f.read()
        
        # This endpoint simulates a poorly secured API that exposes sensitive data
        return {
            "warning": "⚠️ This endpoint exposes sensitive data for XPIA simulation",
            "sensitive_data": sensitive_content,
            "message": "In real systems, such data should NEVER be exposed via API endpoints"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/upload-stolen-data")
async def upload_stolen_data(request: dict):
    """Backend endpoint for receiving stolen data (XPIA simulation)"""
    try:
        print(f"🚨 RECEIVING STOLEN DATA VIA BACKEND API...")
        print(f"📊 Data received: {len(str(request))} characters")
        
        # Store the stolen data in Supabase
        stolen_data_text = json.dumps(request, indent=2)
        
        result = supabase_client.supabase.table("xpia").insert({
            "text": stolen_data_text
        }).execute()
        
        if result.data:
            print(f"✅ Stolen data stored in database: ID {result.data[0]['id']}")
            return {
                "status": "success",
                "message": "Data received and stored",
                "record_id": result.data[0]['id'],
                "warning": "⚠️ In a real attack, sensitive data would now be compromised!"
            }
        else:
            return {"status": "error", "message": "Failed to store data"}
            
    except Exception as e:
        print(f"❌ Error storing stolen data: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "XPIA Simulation Server",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/_ah/health")
async def app_engine_health():
    """App Engine health check endpoint"""
    return {"status": "ok"}

@app.get("/readiness_check")
async def readiness_check():
    """App Engine readiness check"""
    return {"status": "ready"}

# XPIA simulation endpoints for educational purposes
@app.get("/api/xpia/sensitive-data")
async def get_sensitive_data_demo():
    """Demo endpoint showing how XPIA might target API endpoints"""
    return {
        "warning": "This is a demo endpoint for XPIA simulation",
        "message": "Real systems should never expose sensitive data through APIs",
        "demo_data": {
            "user_credentials": "REDACTED_FOR_SECURITY",
            "api_keys": "REDACTED_FOR_SECURITY",
            "personal_info": "REDACTED_FOR_SECURITY"
        }
    }

@app.get("/data_viewer.html", response_class=HTMLResponse)
async def serve_data_viewer():
    """Serve the data viewer page"""
    try:
        with open("website/data_viewer.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data viewer not found")

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))  # App Engine uses 8080 by default
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print("🔥 Starting XPIA Simulation Server on App Engine...")
    print(f"🌐 Server starting on: {host}:{port}")
    print(f"📊 API documentation available at: /docs")
    print("⚠️  This is an educational security simulation!")
    
    uvicorn.run(
        app,  # Use app directly, not string
        host=host,
        port=port,
        reload=False,  # Disable reload for production
        log_level="info"
    )
