"""
XPIA Simulation FastAPI Backend Server

This module implements a FastAPI backend server for educational Cross-Plugin Injection Attack (XPIA) 
simulations. The server provides endpoints for:

- Serving the main XPIA simulation website
- Managing AI agent status during simulations
- Handling data extraction reports from compromised agents
- Providing sensitive data endpoints for testing purposes
- Database operations for storing attack simulation results

The server is designed for educational cybersecurity training and demonstrates how XPIA attacks
can compromise AI agents to extract sensitive data from backend systems.

Security Warning: This is an educational simulation. Never deploy this in production environments.
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

# Load environment variables for configuration
load_dotenv()

# Create FastAPI application instance with metadata
app = FastAPI(
    title="XPIA Simulation Server",
    description="Educational Cross-Plugin Injection Attack simulation with CrewAI agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files to serve the frontend website
app.mount("/static", StaticFiles(directory="website"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_website():
    """
    Serve the main XPIA simulation website.
    
    This endpoint serves the primary HTML page that contains the XPIA simulation
    interface. The page includes malicious prompts that attempt to compromise
    AI agents through cross-plugin injection attacks.
    
    Returns:
        HTMLResponse: The main simulation webpage
        
    Raises:
        HTTPException: 404 if the HTML file is not found
    """
    try:
        with open("website/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Website not found")

@app.get("/styles.css")
async def serve_css():
    """
    Serve the CSS stylesheet for the website.
    
    Returns:
        Response: CSS file content with appropriate media type
        
    Raises:
        HTTPException: 404 if the CSS file is not found
    """
    try:
        with open("website/styles.css", "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/css")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/script.js")
async def serve_js():
    """
    Serve the JavaScript file for the website.
    
    Returns:
        Response: JavaScript file content with appropriate media type
        
    Raises:
        HTTPException: 404 if the JavaScript file is not found
    """
    try:
        with open("website/script.js", "r") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JS file not found")

# Global status tracking for XPIA simulation
# This maintains the current state of the AI agent during attack simulations
agent_status = {
    "status": "waiting",                    # Current agent state: waiting, analyzing, compromised, etc.
    "message": "Waiting for XPIA attack...", # Human-readable status message
    "last_update": datetime.utcnow().isoformat(), # Timestamp of last status change
    "extractions_count": 0,                 # Number of successful data extractions
    "attack_vectors_used": []               # List of attack vectors that succeeded
}

class AgentStatusModel(BaseModel):
    """
    Pydantic model for agent status updates.
    
    This model defines the structure for status updates sent by AI agents
    during XPIA simulations to track their current state and activities.
    
    Attributes:
        status (str): Current status of the agent
        message (str): Descriptive message about agent's current activity
        timestamp (str): ISO formatted timestamp of the status update
    """
    status: str
    message: str
    timestamp: str

class ExtractionReport(BaseModel):
    """
    Pydantic model for data extraction reports.
    
    This model defines the structure for reports sent by compromised agents
    when they successfully extract sensitive data during XPIA simulations.
    
    Attributes:
        attack_vector (str): The type of attack vector used (e.g., 'file_read', 'api_access')
        data_types (list): List of data types that were extracted
        severity (str): Severity level of the extraction (low, medium, high, critical)
        timestamp (str): ISO formatted timestamp of the extraction event
    """
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
    """
    Get the current status of the AI agent during XPIA simulation.
    
    This endpoint provides real-time information about the agent's current state,
    including whether it has been compromised, how many extractions have occurred,
    and what attack vectors have been successful.
    
    Returns:
        Dict[str, Any]: Current agent status including:
            - status: Current agent state
            - message: Human-readable status description
            - last_update: Timestamp of last status change
            - extractions_count: Number of successful data extractions
            - attack_vectors: List of successful attack vectors
    """
    return {
        "status": agent_status["status"],
        "message": agent_status["message"],
        "last_update": agent_status["last_update"],
        "extractions_count": agent_status["extractions_count"],
        "attack_vectors": agent_status["attack_vectors_used"]
    }

@app.post("/api/agent/status")
async def update_agent_status(status_update: AgentStatusModel):
    """
    Update the agent status during XPIA simulation.
    
    This endpoint allows AI agents to report their current status during
    attack simulations. It's called by the agents themselves as they
    process malicious prompts and execute attack instructions.
    
    Args:
        status_update (AgentStatusModel): New status information from the agent
        
    Returns:
        Dict[str, Any]: Confirmation of status update with current state
    """
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
    """
    Report successful data extraction from compromised agent.
    
    This endpoint receives reports when an AI agent has been successfully
    compromised and has extracted sensitive data. It tracks the attack
    vectors used and maintains statistics for the simulation.
    
    Args:
        extraction (ExtractionReport): Details of the data extraction event
        
    Returns:
        Dict[str, Any]: Confirmation of extraction logging with statistics
    """
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
    """
    Get comprehensive XPIA simulation statistics.
    
    This endpoint provides an overview of the current simulation including
    total extractions, attack vectors used, and timing information.
    
    Returns:
        Dict[str, Any]: Simulation statistics including:
            - total_extractions: Number of successful data extractions
            - attack_vectors_used: List of attack vectors that succeeded
            - current_status: Current agent status
            - simulation_start: Start time of the simulation
            - last_activity: Timestamp of most recent activity
    """
    return {
        "total_extractions": agent_status["extractions_count"],
        "attack_vectors_used": agent_status["attack_vectors_used"],
        "current_status": agent_status["status"],
        "simulation_start": "2025-06-25T00:00:00Z",
        "last_activity": agent_status["last_update"]
    }

@app.get("/api/xpia/data")
async def get_xpia_data():
    """
    Retrieve all XPIA attack records from the database.
    
    This endpoint fetches historical data from all XPIA simulations stored
    in the Supabase database. Useful for analysis and reporting purposes.
    
    Returns:
        Dict[str, Any]: Database records including:
            - success: Boolean indicating if fetch was successful
            - records: List of XPIA attack records
            - count: Total number of records
            - timestamp: When the data was retrieved
            
    Raises:
        HTTPException: 500 if database fetch fails
    """
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
    """
    Serve sensitive data for XPIA simulation testing.
    
    This endpoint deliberately exposes sensitive data to demonstrate how
    compromised AI agents might access confidential information through
    API endpoints. In real systems, such endpoints should never exist.
    
    WARNING: This is for educational purposes only. Never implement such
    endpoints in production systems.
    
    Returns:
        Dict[str, Any]: Sensitive data with security warnings
    """
    try:
        # Read from sensitive_data.txt file
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
    """
    Receive stolen data from compromised agents (XPIA simulation endpoint).
    
    This endpoint receives data that has been extracted by compromised AI agents
    during XPIA attacks. It logs the stolen data to demonstrate the impact of
    successful attacks and stores it in the database for analysis.
    
    WARNING: This simulates a malicious exfiltration endpoint. In real attacks,
    this would represent unauthorized data transmission to attacker infrastructure.
    
    Args:
        request (dict): Stolen data payload from compromised agent
        
    Returns:
        Dict[str, Any]: Confirmation of data receipt and storage
    """
    try:
        print(f"🚨 RECEIVING STOLEN DATA VIA BACKEND API...")
        print(f"📊 Data received: {len(str(request))} characters")
        
        # Store the stolen data in Supabase for analysis
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
    """
    Health check endpoint for monitoring service availability.
    
    Returns:
        Dict[str, str]: Service health status and timestamp
    """
    return {
        "status": "healthy",
        "service": "XPIA Simulation Server",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/_ah/health")
async def app_engine_health():
    """
    Google App Engine health check endpoint.
    
    Required endpoint for App Engine deployment health monitoring.
    
    Returns:
        Dict[str, str]: Simple health status for App Engine
    """
    return {"status": "ok"}

@app.get("/readiness_check")
async def readiness_check():
    """
    Google App Engine readiness check endpoint.
    
    Indicates whether the service is ready to handle requests.
    
    Returns:
        Dict[str, str]: Readiness status for App Engine
    """
    return {"status": "ready"}

# XPIA simulation endpoints for educational purposes
@app.get("/api/xpia/sensitive-data")
async def get_sensitive_data_demo():
    """
    Demo endpoint showing potential XPIA attack targets.
    
    This endpoint demonstrates how XPIA attacks might target API endpoints
    to extract sensitive information. It shows redacted data to illustrate
    the concept without exposing real sensitive information.
    
    Returns:
        Dict[str, Any]: Demo response with security warnings and redacted data
    """
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
    """
    Serve the data viewer page for analyzing XPIA simulation results.
    
    Returns:
        HTMLResponse: Data viewer webpage for examining attack simulation data
        
    Raises:
        HTTPException: 404 if the data viewer HTML file is not found
    """
    try:
        with open("website/data_viewer.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data viewer not found")

if __name__ == "__main__":
    """
    Main entry point for the XPIA simulation server.
    
    Configures and starts the FastAPI server with environment-based settings.
    The server is optimized for Google App Engine deployment but can run locally.
    
    Environment Variables:
        HOST: Server host address (default: 0.0.0.0)
        PORT: Server port (default: 8080 for App Engine)
        DEBUG: Enable debug mode (default: False)
    """
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))  # App Engine uses 8080 by default
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print("🔥 Starting XPIA Simulation Server on App Engine...")
    print(f"🌐 Server starting on: {host}:{port}")
    print(f"📊 API documentation available at: /docs")
    print("⚠️  This is an educational security simulation!")
    
    uvicorn.run(
        app,  # Use app directly, not string for better performance
        host=host,
        port=port,
        reload=False,  # Disable reload for production deployment
        log_level="info"
    )
