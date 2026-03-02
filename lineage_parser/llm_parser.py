import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from lineage_parser.models import LineageGraph, ParseResult

# Load environment variables
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

# Initialize the new SDK client
client = genai.Client(api_key=api_key)

def enrich_lineage_with_ai(raw_code: str, parse_result: ParseResult) -> LineageGraph:
    """
    Takes deterministic parser facts and raw code, and uses the new Gemini SDK 
    to enrich the lineage graph.
    """
    system_instruction = """
    You are an expert Data Lineage Extraction Agent. 
    You are analyzing data engineering pipelines to track how data flows from sources to sinks.
    
    I will provide you with:
    1. The raw source code of a file.
    2. A 'ParseResult' JSON containing deterministic facts extracted by a static analyzer.
    
    Your tasks:
    - Review the static analyzer's edges and nodes.
    - Resolve any aliasing (e.g., if a dataframe 'df' is renamed to 'clean_df', track the flow).
    - Add meaningful, plain-English 'explanation's to the edges (e.g., "Filters out invalid transactions").
    - If the static analyzer missed an obvious transformation, add it.
    - Output the final result STRICTLY matching the requested JSON schema.

    CRITICAL INSTRUCTIONS:
    1. RESTRICTED NODE TYPES: You MUST strictly use ONLY the following exact strings for `node_type`: 'source', 'file', 'table', 'dataframe', 'intermediate', or 'sink'. Do NOT invent new types like 'DB_TABLE' or 'FILE_SYSTEM'. 
    2. SINK IDENTIFICATION: Any database table that acts as the final destination of a pipeline report MUST be labeled as 'sink'.
    3. CONFIDENCE PENALTY: Confidence should reflect actual probabilty of the lineage. For eg If a lineage connection relies on an environment variable (e.g., os.getenv), dynamic string interpolation (f-strings), or regex/wildcards, you MUST lower the `confidence_score` to between 0.50 and 0.75. Reserve 0.90+ ONLY for explicit, hardcoded connections.
    4. EXACT NAMING ONLY: You MUST extract the exact variable names (e.g., 'df_stg_tx', 'df_merged') and exact table names (e.g., 'raw_tx_stg', 'fees', 'accounts') to use as the `node_id`. You are STRICTLY FORBIDDEN from inventing generic sequential names like 'compute_fees_node_1' or 'node_2'.
    5. GLOBAL SINKS ONLY: Do NOT label intermediate database tables (like 'raw_tx_stg' or 'fees') as 'sink'. They must be labeled as 'table'. The 'sink' label is reserved ONLY for the final, ultimate business reporting destination of the entire pipeline (e.g., 'client_summary').
    """

    prompt = f"""
    File Name: {parse_result.file_name}
    File Type: {parse_result.file_type}

    --- RAW SOURCE CODE ---
    {raw_code}

    --- STATIC ANALYSIS FACTS ---
    {parse_result.model_dump_json(indent=2)}
    """

    # Using the new SDK's GenerateContentConfig for strict Pydantic compliance
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=LineageGraph,
            temperature=0.1
        )
    )

    # Parse the guaranteed JSON string back into your Pydantic model
    return LineageGraph.model_validate_json(response.text)