"""
Master Notebook Generator for The Databricks Handbook
Executes all 10 module generators to create all 105 Databricks source notebooks.
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

import gen_mod01
import gen_mod02
import gen_mod03
import gen_mod04
import gen_mod05
import gen_mod06
import gen_mod07
import gen_mod08
import gen_mod09
import gen_mod10

def main():
    base_dir = scripts_dir.parent
    print(f"=== Generating The Databricks Handbook (105 Notebooks) at {base_dir} ===")
    
    modules = [
        gen_mod01,
        gen_mod02,
        gen_mod03,
        gen_mod04,
        gen_mod05,
        gen_mod06,
        gen_mod07,
        gen_mod08,
        gen_mod09,
        gen_mod10
    ]
    
    total = 0
    for idx, mod in enumerate(modules, 1):
        print(f"\n--- Running Module {idx:02d} Generator ---")
        mod.generate(base_dir)
        
    all_notebooks = list((base_dir / "notebooks").glob("*/*.py"))
    print(f"\n========================================================")
    print(f"Successfully generated {len(all_notebooks)} Databricks notebooks across 10 modules!")
    print(f"========================================================")
    assert len(all_notebooks) == 105, f"Expected 105 notebooks, found {len(all_notebooks)}"

if __name__ == "__main__":
    main()
