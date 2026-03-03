import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import your core logic from the lineage_parser module
from lineage_parser.process import get_or_generate_raw_lineage, resolve_entities

app = FastAPI(title="LineageGuard.ai Generator API")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration Paths
CORPUS_DIR = "./corpus"
RAW_CACHE_FILE = "raw_lineage_cache.json"
# FIXED: Route the stitched file into the corpus directory
STITCHED_FILE = Path(CORPUS_DIR) / "stitched_lineage.json"

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
        
        # 3. Save the final JSON for the frontend into the corpus folder
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
    # FIXED: Check the path inside the corpus folder
    if not STITCHED_FILE.exists():
        raise HTTPException(
            status_code=404, 
            detail="Lineage graph not found. Please click 'Run Lineage Generation' first."
        )
        
    try:
        with open(STITCHED_FILE, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading lineage file: {str(e)}")