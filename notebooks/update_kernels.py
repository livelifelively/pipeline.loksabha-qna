import json
import glob
import os

def update_notebook_kernel(notebook_path):
    with open(notebook_path, 'r') as f:
        notebook = json.load(f)
    
    # Update kernel spec
    notebook['metadata']['kernelspec'] = {
        "display_name": "notebooks.venv",
        "language": "python",
        "name": "notebooks.venv"
    }
    
    with open(notebook_path, 'w') as f:
        json.dump(notebook, f, indent=1)

# Update all .ipynb files in the notebooks directory
for notebook in glob.glob('*.ipynb'):
    print(f"Updating kernel for {notebook}")
    update_notebook_kernel(notebook) 