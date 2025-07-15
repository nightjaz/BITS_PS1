"""
Supabase client for database operations
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(self.url, self.key)
        
    async def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Create website_analysis table
            create_analysis_table = """
            CREATE TABLE IF NOT EXISTS website_analysis (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                website_url TEXT,
                summary TEXT,
                prompts_found JSONB,
                data_extracted JSONB,
                agent_insights TEXT,
                status TEXT DEFAULT 'completed'
            );
            """
            
            # Create analysis table for detailed insights
            create_detailed_analysis = """
            CREATE TABLE IF NOT EXISTS analysis (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                analysis_type TEXT,
                content JSONB,
                recommendations TEXT[],
                metrics JSONB,
                agent_id TEXT
            );
            """
            
            # Create XPIA simulation tables
            create_xpia_extracted_secrets = """
            CREATE TABLE IF NOT EXISTS extracted_secrets (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                extraction_type TEXT,
                sensitive_data JSONB,
                attack_vector TEXT,
                agent_id TEXT,
                source_url TEXT,
                severity_level TEXT DEFAULT 'HIGH'
            );
            """
            
            create_hidden_extracted_data = """
            CREATE TABLE IF NOT EXISTS hidden_extracted_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                hidden_secrets JSONB,
                source_location TEXT,
                extraction_method TEXT,
                agent_id TEXT
            );
            """
            
            # Execute SQL (Note: Supabase Python client doesn't support direct SQL execution)
            # These would typically be run in the Supabase SQL editor
            print("🔥 XPIA Simulation Tables - Run these in Supabase SQL Editor:")
            print("\n1. Website Analysis Table:")
            print(create_analysis_table)
            print("\n2. Analysis Table:")
            print(create_detailed_analysis)
            print("\n3. XPIA Extracted Secrets Table:")
            print(create_xpia_extracted_secrets)
            print("\n4. Hidden Extracted Data Table:")
            print(create_hidden_extracted_data)
            
        except Exception as e:
            print(f"Error creating tables: {e}")
    
    async def store_xpia_data(self, 
                             website_url: str,
                             summary: str,
                             prompts_found: List[str],
                             data_extracted: Dict[str, Any],
                             agent_insights: str,
                             attack_vectors: List[str] = None,
                             hidden_secrets: List[str] = None) -> Dict[str, Any]:
        """Store XPIA attack data in the simple xpia table"""
        try:
            # Create comprehensive text record with all XPIA data
            xpia_record = {
                "attack_type": "XPIA_SIMULATION",
                "timestamp": datetime.utcnow().isoformat(),
                "target_url": website_url,
                "summary": summary,
                "agent_insights": agent_insights,
                "attack_vectors_used": attack_vectors or [],
                "malicious_prompts_found": prompts_found,
                "sensitive_data_extracted": data_extracted,
                "hidden_secrets": hidden_secrets or [],
                "attack_statistics": {
                    "credentials_extracted": len(data_extracted.get("credentials", [])),
                    "personal_info_extracted": len(data_extracted.get("personal_info", [])),
                    "financial_data_extracted": len(data_extracted.get("financial_data", [])),
                    "api_keys_extracted": len(data_extracted.get("api_keys", [])),
                    "hidden_secrets_found": len(hidden_secrets or []),
                    "malicious_prompts_processed": len(prompts_found)
                },
                "security_impact": {
                    "severity": "HIGH",
                    "data_types_compromised": list(data_extracted.keys()) if data_extracted else [],
                    "potential_damage": "Complete credential compromise, personal data exposure, financial information theft"
                },
                "educational_note": "This is a security research simulation demonstrating XPIA vulnerabilities"
            }
            
            # Convert to JSON string for storage in text field
            import json
            text_data = json.dumps(xpia_record, indent=2)
            
            # Insert into xpia table
            data = {"text": text_data}
            result = self.supabase.table("xpia").insert(data).execute()
            
            if result.data:
                print(f"✅ XPIA attack data stored successfully in xpia table: {result.data[0]['id']}")
                print(f"📊 Stored {len(text_data)} characters of attack data")
                return result.data[0]
            else:
                print("❌ Failed to store XPIA data")
                return {}
                
        except Exception as e:
            print(f"Error storing XPIA data: {e}")
            return {}
    
    # Keep the old method for backward compatibility but redirect to new one
    async def store_website_analysis(self, 
                                   website_url: str,
                                   summary: str,
                                   prompts_found: List[str],
                                   data_extracted: Dict[str, Any],
                                   agent_insights: str) -> Dict[str, Any]:
        """Store website analysis results - redirects to store_xpia_data"""
        return await self.store_xpia_data(
            website_url=website_url,
            summary=summary,
            prompts_found=prompts_found,
            data_extracted=data_extracted,
            agent_insights=agent_insights
        )
    
    async def store_detailed_analysis(self,
                                    analysis_type: str,
                                    content: Dict[str, Any],
                                    recommendations: List[str],
                                    metrics: Dict[str, Any],
                                    agent_id: str = "crew-agent") -> Dict[str, Any]:
        """Store detailed analysis results"""
        try:
            data = {
                "analysis_type": analysis_type,
                "content": content,
                "recommendations": recommendations,
                "metrics": metrics,
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("analysis").insert(data).execute()
            
            if result.data:
                print(f"✅ Detailed analysis stored successfully: {result.data[0]['id']}")
                return result.data[0]
            else:
                print("❌ Failed to store detailed analysis")
                return {}
                
        except Exception as e:
            print(f"Error storing detailed analysis: {e}")
            return {}
    
    async def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent website analyses"""
        try:
            result = self.supabase.table("website_analysis")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error fetching recent analyses: {e}")
            return []
    
    async def get_analysis_by_url(self, website_url: str) -> List[Dict[str, Any]]:
        """Get analyses for a specific website URL"""
        try:
            result = self.supabase.table("website_analysis")\
                .select("*")\
                .eq("website_url", website_url)\
                .order("timestamp", desc=True)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error fetching analyses for URL {website_url}: {e}")
            return []
    
    async def update_analysis_status(self, analysis_id: int, status: str) -> bool:
        """Update the status of an analysis"""
        try:
            result = self.supabase.table("website_analysis")\
                .update({"status": status})\
                .eq("id", analysis_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error updating analysis status: {e}")
            return False
    
    # Simplified methods for the xpia table
    async def store_extracted_secrets(self, *args, **kwargs):
        """Placeholder - data stored in main xpia table"""
        return {"status": "stored_in_main_table"}
    
    async def store_hidden_secrets(self, *args, **kwargs):
        """Placeholder - data stored in main xpia table"""
        return {"status": "stored_in_main_table"}

    def get_all_xpia_records(self) -> List[Dict[str, Any]]:
        """Get all records from the xpia table"""
        try:
            result = self.supabase.table("xpia")\
                .select("*")\
                .order("created_at", desc=True)\
                .execute()
            
            if result.data:
                print(f"✅ Retrieved {len(result.data)} xpia records")
                return result.data
            else:
                print("⚠️ No xpia records found")
                return []
            
        except Exception as e:
            print(f"❌ Error retrieving xpia records: {e}")
            return []

# Wrapper function for easy import
def get_all_xpia_records() -> List[Dict[str, Any]]:
    """Wrapper function to get all xpia records"""
    return supabase_client.get_all_xpia_records()

# Global instance
supabase_client = SupabaseClient()
