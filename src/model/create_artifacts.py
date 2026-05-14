import tarfile
from pathlib import Path

# Resolve directory where this script lives
try:
    base_dir = Path(__file__).resolve().parent
except NameError:
    # Fallback for Jupyter
    base_dir = Path.cwd()

# Files to include
files_to_add = [
    "pipeline.joblib",
    "inference.py",
    "requirements.txt",
]

# Output tar path (same directory)
tar_path = base_dir / "model.tar.gz"


def main():
    with tarfile.open(tar_path, "w:gz") as tar:
        for file_name in files_to_add:
            file_path = base_dir / file_name
            
            if not file_path.exists():
                raise FileNotFoundError(f"Missing file: {file_path}")
            
            # arcname ensures clean structure inside the tar
            tar.add(file_path, arcname=file_name)

    print(f"model.tar.gz created successfully at: {tar_path}")


if __name__ == "__main__":
    main()
