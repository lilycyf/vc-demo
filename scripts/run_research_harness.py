"""Universal research-session CLI. Task providers own data and model specifics."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from vc_demo.harness.research_v2.cli import main

if __name__=='__main__':
    main()
