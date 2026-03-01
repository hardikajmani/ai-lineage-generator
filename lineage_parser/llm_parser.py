import json
import google.genai as genai
from lineage_parser.models import LineageGraph, ParseResult
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Retrieve the key securely
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

# Configure the SDK
genai.configure(api_key=api_key)

def enrich_lineage_with_ai(raw_code: str, parse_result: ParseResult) -> LineageGraph:
    """
    Takes deterministic parser facts and raw code, and uses an LLM to enrich 
    the lineage graph, resolving ambiguities and adding explanations.
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
    - If the static analyzer missed an obvious transformation (e.g., a Pandas merge or aggregation), add it.
    - Output the final result STRICTLY matching the requested JSON schema.
    """

    prompt = f"""
    File Name: {parse_result.file_name}
    File Type: {parse_result.file_type}

    --- RAW SOURCE CODE ---
    {raw_code}

    --- STATIC ANALYSIS FACTS ---
    {parse_result.model_dump_json(indent=2)}
    """

    # Using Gemini's Structured Outputs to guarantee Pydantic compliance
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction
    )

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=LineageGraph,
            temperature=0.1 # Keep it deterministic
        )
    )

    # Parse the guaranteed JSON string back into your Pydantic model
    return LineageGraph.model_validate_json(response.text)