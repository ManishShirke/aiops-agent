import asyncio
import os
import sys
import nest_asyncio

# Ensure we can import local modules
sys.path.append(os.getcwd())

# --- CONFIGURATION ---
import google.generativeai as genai
if "GOOGLE_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
else:
    print("⚠️ WARNING: No Google API Key found. Set os.environ['GOOGLE_API_KEY']")

from aiops_agent.infrastructure.state_store import STATE
from aiops_agent.orchestrator.ops_orchestrator import OpsOrchestrator

nest_asyncio.apply()

async def main():
    print("\n⚙️  [System] Seeding Database to demonstrate RAG & Compaction...")
    STATE.archive_incident("payments-api latency", "scale_pods")
    STATE.archive_incident("Incident A", "Reboot")
    STATE.archive_incident("Incident B", "Patch")
    STATE.archive_incident("Incident C", "Scale") # Triggers Compaction!
    
    # Initialize Logic
    orchestrator = OpsOrchestrator()
    
    # Define Input Scenario
    input_text = "payments-api experiencing latency spikes."
    print(f"\n🚀 Starting Interactive Session: '{input_text}'")
    print("   (The system will pause for your input when tools are called)\n")

    # --- DIRECT EXECUTION ---
    # FIX: Since orchestrator.run() returns a single result (not a stream),
    # we simply await it.
    await orchestrator.run(input_text)

    print("\n🏁 Session Complete.")

if __name__ == "__main__":
    asyncio.run(main())
