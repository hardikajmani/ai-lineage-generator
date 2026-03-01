import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import your core logic from the lineage_parser module
from lineage_parser.process import get_or_generate_raw_lineage, resolve_entities

app = FastAPI(title="AI Lineage Generator API")

# --- CORS Middleware ---
# This is required so your Vite/React frontend (running on localhost:5173) 
# can securely make requests to this API (running on localhost:8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration Paths
CORPUS_DIR = "./corpus"
RAW_CACHE_FILE = "raw_lineage_cache.json"
STITCHED_FILE = "stitched_lineage.json"

@app.post("/api/generate")
def generate_lineage():
    """
    Triggers the lineage generation process. 
    It respects the caching mechanism to save LLM API calls, 
    applies entity resolution, and saves the stitched graph.
    """
    try:
        # 1. Generate or load the raw graph
        raw_lineage = get_or_generate_raw_lineage(CORPUS_DIR, RAW_CACHE_FILE)
        
        # 2. Stitch the entities together
        stitched_lineage = resolve_entities(raw_lineage)
        
        # 3. Save the final JSON for the frontend
        with open(STITCHED_FILE, "w") as f:
            f.write(stitched_lineage.model_dump_json(indent=2))
            
        return {
            "status": "success", 
            "message": "Lineage generated and stitched successfully.",
            "nodes_count": len(stitched_lineage.nodes),
            "edges_count": len(stitched_lineage.edges)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/api/lineage")
def get_lineage():
    """
    Serves the pre-computed, stitched lineage graph to the frontend UI.
    """
    path = Path(STITCHED_FILE)
    
    if not path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Lineage graph not found. Please call /api/generate first."
        )
        
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading lineage file: {str(e)}")