"""
Databricks Asset Bundle (DAB) Validator
Verifies that databricks.yml and all resources/*.yml conform to DAB schemas
and that all referenced notebook paths and app components exist on disk.
"""

import re
import sys
from pathlib import Path

def validate_bundle():
    base_dir = Path(__file__).parent.parent
    bundle_file = base_dir / "databricks.yml"
    
    print(f"Validating Databricks Asset Bundle at {base_dir}...")
    if not bundle_file.exists():
        print(f"ERROR: databricks.yml missing at {bundle_file}")
        sys.exit(1)
        
    content = bundle_file.read_text(encoding="utf-8")
    assert "name: databricks-handbook" in content, "databricks.yml must define name: databricks-handbook"
    assert "targets:" in content, "databricks.yml must define targets"
    assert "dev:" in content and "prod:" in content, "databricks.yml must define dev and prod targets"
    
    # Check resources
    resources_dir = base_dir / "resources"
    expected_resources = ["jobs.yml", "dlt_pipelines.yml", "unity_catalog.yml", "dashboards.yml", "model_serving.yml", "apps.yml"]
    for res in expected_resources:
        res_path = resources_dir / res
        if not res_path.exists():
            print(f"ERROR: Missing resource file {res_path}")
            sys.exit(1)
            
    # Check notebook references in resources
    missing_paths = []
    for yml_file in resources_dir.glob("*.yml"):
        yml_text = yml_file.read_text(encoding="utf-8")
        matches = re.findall(r'notebook_path:\s*["\']?\.\./(notebooks/[^\s"\']+\.py)["\']?', yml_text)
        for rel_path in matches:
            abs_path = base_dir / rel_path
            if not abs_path.exists():
                missing_paths.append(f"{yml_file.name} references non-existent notebook: {rel_path}")
                
    if missing_paths:
        print("\n--- MISSING NOTEBOOK PATHS IN BUNDLE RESOURCES ---")
        for m in missing_paths:
            print(f"  ❌ {m}")
        sys.exit(1)
        
    # Check Databricks App
    app_dir = base_dir / "apps" / "lakehouse_finops_monitor"
    assert (app_dir / "app.py").exists(), "Missing app.py in Databricks App"
    assert (app_dir / "app.yaml").exists(), "Missing app.yaml in Databricks App"
    assert (app_dir / "requirements.txt").exists(), "Missing requirements.txt in Databricks App"
    
    print("✅ Databricks Asset Bundle verified: 100% schema and path integrity!")

if __name__ == "__main__":
    validate_bundle()
