import os
import sys
import glob
import subprocess
from concurrent.futures import ProcessPoolExecutor

def process_obj(file_path, dest_dir):
    print(f"Processing {file_path} ...")
    cmd = [
        "blender",
        "phong.blend",
        "--background",
        "--python", "phong.py",
        "--",
        file_path,
        dest_dir
    ]
    dir_created = os.path.join(dest_dir, os.path.basename(file_path).replace(".obj", ""))
    if os.path.exists(dir_created):
        print('skipping existing dir', dir_created)
        return 0
    else:
        return subprocess.run(cmd, check=True)

def main(src_dir, dest_dir, max_workers=None):
    os.makedirs(dest_dir, exist_ok=True)
    obj_files = glob.glob(os.path.join(src_dir, "*.obj"))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_obj, f, dest_dir) for f in obj_files]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Error processing file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: mv_hipp_run.py <SRC_DIR> <DEST_DIR> [MAX_WORKERS]")
        sys.exit(1)
    src_dir = sys.argv[1]
    dest_dir = sys.argv[2]
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else None
    main(src_dir, dest_dir, max_workers)