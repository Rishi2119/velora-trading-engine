import os
import re

dirs = [r'D:\trading_engins\Velora_Ai\data', r'D:\trading_engins\Velora_Ai\ai', r'D:\trading_engins\Velora_Ai\api', r'D:\trading_engins\Velora_Ai\tests']
for d in dirs:
    os.makedirs(d, exist_ok=True)

with open(r'c:\Users\rishi\Downloads\FOREX_STRATEGY_AI_TRAINING.md', 'r', encoding='utf-8') as f:
    content = f.read()

# EXTRACT JSON
json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
if json_match:
    with open(r'D:\trading_engins\Velora_Ai\data\strategies.json', 'w', encoding='utf-8') as out:
        out.write(json_match.group(1))
    print('Saved strategies.json')

# EXTRACT preprocess.py
prep_match = re.search(r'### Step 2 — Create `ai/preprocess\.py`.*?```python\n(.*?)```', content, re.DOTALL)
if prep_match:
    with open(r'D:\trading_engins\Velora_Ai\ai\preprocess.py', 'w', encoding='utf-8') as out:
        out.write(prep_match.group(1))
    print('Saved preprocess.py')

# EXTRACT train_model.py
train_match = re.search(r'### Step 3 — Create `ai/train_model\.py`.*?```python\n(.*?)```', content, re.DOTALL)
if train_match:
    with open(r'D:\trading_engins\Velora_Ai\ai\train_model.py', 'w', encoding='utf-8') as out:
        out.write(train_match.group(1))
    print('Saved train_model.py')

# EXTRACT strategy_score.py
score_match = re.search(r'### Step 4 — Create `api/strategy_score\.py`.*?```python\n(.*?)```', content, re.DOTALL)
if score_match:
    with open(r'D:\trading_engins\Velora_Ai\api\strategy_score.py', 'w', encoding='utf-8') as out:
        out.write(score_match.group(1))
    print('Saved strategy_score.py')

# EXTRACT test_ai_pipeline.py
test_match = re.search(r'### Step 5 — Create `tests/test_ai_pipeline\.py`.*?```python\n(.*?)```', content, re.DOTALL)
if test_match:
    with open(r'D:\trading_engins\Velora_Ai\tests\test_ai_pipeline.py', 'w', encoding='utf-8') as out:
        out.write(test_match.group(1))
    print('Saved test_ai_pipeline.py')
