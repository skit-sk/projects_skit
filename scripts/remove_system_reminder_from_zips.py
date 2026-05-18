#!/usr/bin/env python3
import os, zipfile, io, re, shutil

BASE_ZIPS = [
  'workspace/part-aa.zip', 'workspace/part-ab.zip', 'workspace/part-ac.zip',
  'workspace/part-ad.zip', 'workspace/part-ae.zip', 'workspace/part-af.zip'
]

def remove_block_from_text(text: str) -> str:
    return re.sub(r"<system-reminder>[\s\S]*?</system-reminder>\s*", "", text)

def process_archive(zip_path: str):
    base = os.path.basename(zip_path)
    extract_dir = f"/tmp/extract_{base}"
    if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)
    found = False
    for root, dirs, files in os.walk(extract_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue
            if '<system-reminder>' in content:
                new_content = remove_block_from_text(content)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                found = True
    if not found:
        print(f'No system-reminder blocks found in {zip_path}')
        shutil.rmtree(extract_dir)
        return
    new_zip = zip_path + '.new'
    with zipfile.ZipFile(new_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for folder, _, files in os.walk(extract_dir):
            for file in files:
                full = os.path.join(folder, file)
                arc = os.path.relpath(full, extract_dir)
                z.write(full, arc)
    os.replace(new_zip, zip_path)
    shutil.rmtree(extract_dir)
    print('Updated', zip_path)

def main():
    for z in BASE_ZIPS:
        if os.path.exists(z):
            process_archive(z)
        else:
            print('Not found:', z)

if __name__ == '__main__':
    main()
