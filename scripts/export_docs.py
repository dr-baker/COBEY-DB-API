"""Script to export API documentation in various formats."""
import json
import os
import requests
from pathlib import Path
from typing import Optional

def export_openapi_json(host: str = "http://localhost:8000", output_dir: str = "docs") -> None:
    """Export OpenAPI JSON schema."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Fetch OpenAPI schema
    response = requests.get(f"{host}/openapi.json")
    response.raise_for_status()
    
    # Save JSON file
    output_path = Path(output_dir) / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(response.json(), f, indent=2)
    print(f"OpenAPI JSON schema exported to {output_path}")

def export_swagger_ui(host: str = "http://localhost:8000", output_dir: str = "docs") -> None:
    """Export Swagger UI HTML."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Fetch Swagger UI HTML
    response = requests.get(f"{host}/docs")
    response.raise_for_status()
    
    # Save HTML file
    output_path = Path(output_dir) / "swagger.html"
    with open(output_path, "w") as f:
        f.write(response.text)
    print(f"Swagger UI HTML exported to {output_path}")

def export_redoc(host: str = "http://localhost:8000", output_dir: str = "docs") -> None:
    """Export ReDoc HTML."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Fetch ReDoc HTML
    response = requests.get(f"{host}/redoc")
    response.raise_for_status()
    
    # Save HTML file
    output_path = Path(output_dir) / "redoc.html"
    with open(output_path, "w") as f:
        f.write(response.text)
    print(f"ReDoc HTML exported to {output_path}")

def main(host: Optional[str] = None, output_dir: str = "docs") -> None:
    """Export API documentation in various formats."""
    if host is None:
        host = "http://localhost:8000"
    
    try:
        export_openapi_json(host, output_dir)
        export_swagger_ui(host, output_dir)
        export_redoc(host, output_dir)
        print("\nDocumentation exported successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not connect to {host}")
        print("Make sure the FastAPI server is running.")
        print(f"Error details: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export API documentation")
    parser.add_argument("--host", help="API host URL (default: http://localhost:8000)")
    parser.add_argument("--output-dir", default="docs", help="Output directory (default: docs)")
    
    args = parser.parse_args()
    main(args.host, args.output_dir) 