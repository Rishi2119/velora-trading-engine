import os, json, urllib.request, urllib.error

# Find Expo session files
expo_dir = os.path.expanduser("~/.expo")
print("Expo dir:", expo_dir)
if os.path.exists(expo_dir):
    print("Files:", os.listdir(expo_dir))
    for fname in os.listdir(expo_dir):
        fpath = os.path.join(expo_dir, fname)
        try:
            content = open(fpath).read()
            print(f"\n--- {fname} ---")
            print(content[:500])
        except Exception as e:
            print(f"  Error reading {fname}: {e}")
else:
    print("~/.expo does not exist")

# Try EAS global dir
for alt in [
    os.path.expanduser("~/.eas"),
    os.path.join(os.environ.get("APPDATA",""), "eas"),
    os.path.join(os.environ.get("APPDATA",""), "expo"),
    os.path.join(os.environ.get("LOCALAPPDATA",""), "eas"),
]:
    if os.path.exists(alt):
        print(f"\nFound: {alt}")
        print(os.listdir(alt))
