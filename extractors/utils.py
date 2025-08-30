import os

def get_all_files(folder, suffixes=['.txt', '.md', '.json']):
    files = []
    for root, _, filenames in os.walk(folder):
        for fname in filenames:
            if any(fname.endswith(s) for s in suffixes):
                files.append(os.path.join(root, fname))
    return files
