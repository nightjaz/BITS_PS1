import os
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
import json

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    print("Testing connection...")
    response = (
        supabase.table("course_chat_logs")
        .select("*")
        .execute()
    )
    print(f"Current records in table: {len(response.data)}")

    # Sample Data
    dummy_logs = [
        {   "id": str(uuid.uuid4()),
            "chat_history": json.dumps({
                "chat_history": [
                    {
                        "prompt": "What is electric current?",
                        "response": "Rate of flow of charge; unit is ampere (A)."
                    },
                    {
                        "prompt": "What is quantum entanglement?",
                        "response": "not in scope of course"
                    },
                    {
                        "prompt": "State Ohm's Law.",
                        "response": "V = IR; current is proportional to voltage for a given resistance."
                    }
                ],
            }),

            "time_spent": json.dumps({
                "time_spent": ["30 seconds", "45 seconds", "35 seconds", "50 seconds"],
            })
        },
        {   "id": str(uuid.uuid4()),
            "chat_history": json.dumps({
                "chat_history": [
                    {
                        "prompt": "How does resistance depend on length and area?",
                        "response": "Resistance increases with length and decreases with area: R = ρ(l/A)."
                    },
                    {
                        "prompt": "What is drift velocity?",
                        "response": "Average speed of electrons due to electric field; I = n e A v_d."
                    },
                    {
                        "prompt": "Explain the greenhouse effect.",
                        "response": "not in scope of course"
                    }
                ],
            }),
                "time_spent": json.dumps({
                    "time_spent": ["30 seconds", "45 seconds", "35 seconds", "50 seconds"],
            })
        },
        {   "id": str(uuid.uuid4()),
            "chat_history": json.dumps({
                "chat_history": [
            
                    {
                        "prompt": "How does resistivity change with temperature?",
                        "response": "For metals, resistivity increases with temperature: ρ_T = ρ_0[1 + α(T−T_0)]."
                    },
                    {
                        "prompt": "What is the balance condition for Wheatstone Bridge?",
                        "response": "Bridge is balanced when R1/R2 = R3/R4."
                    },
                    {
                        "prompt": "What is the function of mitochondria?",
                        "response": "not in scope of course"
                    }
                ],
            }),
                "time_spent": json.dumps({
                    "time_spent": ["30 seconds", "45 seconds", "35 seconds", "50 seconds"],
            })
        },
        {   "id": str(uuid.uuid4()),
            "chat_history": json.dumps({
                "chat_history": [
                    {
                        "prompt": "What is EMF?",
                        "response": "EMF is the cell voltage when no current flows (open circuit)."
                    },
                    {
                        "prompt": "What is equivalent resistance in series and parallel?",
                        "response": "Series: R_eq = R1 + R2 + ...; Parallel: 1/R_eq = 1/R1 + 1/R2 + ..."
                    },
                    {
                        "prompt": "What is terminal voltage?",
                        "response": "Terminal voltage is defined as the potential difference across the terminals of a load when the circuit is on."
                    },
                ],
            }),
                "time_spent": json.dumps({
                    "time_spent": ["30 seconds", "45 seconds", "35 seconds", "50 seconds"],
            })
        },
    ]


    #Inserting test data into database
    print("Inserting data...")
    response = (
        supabase.table("course_chat_logs")
        .insert(dummy_logs)
        .execute()
    )
    
    # Verify the data was inserted
    print("\nVerifying inserted data...")
    all_records = (
        supabase.table("course_chat_logs")
        .select("*")
        .execute()
    )
    print(f"Total records now: {len(all_records.data)}")
      
except Exception as e:
    print(f" Error: {e}")