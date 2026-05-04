import os
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py') or file == '.env':
            path = os.path.join(root, file)
            try:
                with open(path, 'rb') as f:
                    if b'\0' in f.read():
                        print(f"FOUND NULL IN: {path}")
            except Exception:
                pass
