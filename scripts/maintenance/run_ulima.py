import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from core.universal_harvester import main, UniversalHarvester
import json
import argparse
from unittest.mock import patch

inst_json = {
    "id": "ccd04100-1bde-427b-b94f-ab24ae233a2a",
    "name": "Universidad de Lima",
    "website_url": "https://www.ulima.edu.pe"
}

# Injecting args via sys.argv mock
test_args = ["universal_harvester.py", json.dumps(inst_json)]
with patch.object(sys, 'argv', test_args):
    asyncio.run(main())