import os
import re
from pathlib import Path

ROOT = Path(r"D:\trading_engins\Velora_Ai")

with open(r'c:\Users\rishi\Downloads\FOREX_STRATEGY_AI_TRAINING.md', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"\*\*File\*\*: `([^`]+)`[^\n]*\n+```(?:python|sql|bash)\n(.*?)\n```"

for match in re.finditer(pattern, content, re.DOTALL):
    filepath = match.group(1).replace('/', '\\')
    code = match.group(2)
    
    full_path = ROOT / filepath
    
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as out:
        out.write(code)
    print(f"Created {full_path}")
