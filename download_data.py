import os
import re
import requests
from pathlib import Path
from typing import List, Tuple

def get_r_function_content(owner: str, repo: str, function_num: int) -> str:
    """Fetch the content of an R function file from GitHub."""
    # Format number with leading zeros
    padded_num = str(function_num).zfill(4)
    filename = f"data{padded_num}.R"
    
    # Use requests to get the raw content
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/R/data/{filename}"
    response = requests.get(url)
    if response.status_code == 404:
        return None
    return response.text

def extract_download_urls(r_content: str) -> List[Tuple[str, str]]:
    """Extract download URLs and their associated filenames from R function content."""
    if not r_content:
        return []
    
    # Pattern to match download.file() calls
    # This handles both single quotes and double quotes
    pattern = r"download\.file\(([\'\"])(.*?)\1.*?destfile\s*=\s*.*?([\'\"])(.*?)\3"
    matches = re.finditer(pattern, r_content, re.DOTALL)
    
    urls = []
    for match in matches:
        url = match.group(2)
        filename = os.path.basename(match.group(4).replace("paste0(folder, '", "").replace("')", ""))
        urls.append((url, filename))
    
    return urls

def download_file(url: str, folder: Path, filename: str) -> bool:
    """Download a file from URL to specified folder."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        file_path = folder / filename
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def main():
    # Configuration
    owner = "jc9677"
    repo = "ceanav"
    base_folder = Path("downloads")  # Change this to your desired base folder
    
    # Create base folder if it doesn't exist
    base_folder.mkdir(exist_ok=True)
    
    # Process each function from 1 to 88
    for i in range(1, 89):
        # Get the R function content
        r_content = get_r_function_content(owner, repo, i)
        if not r_content:
            print(f"Could not find data{str(i).zfill(4)}.R")
            continue
        
        # Create folder for this dataset
        dataset_folder = base_folder / f"data{str(i).zfill(4)}"
        dataset_folder.mkdir(exist_ok=True)
        
        # Extract and download URLs
        urls = extract_download_urls(r_content)
        if not urls:
            print(f"No download URLs found in data{str(i).zfill(4)}.R")
            continue
            
        print(f"\nProcessing data{str(i).zfill(4)}:")
        for url, filename in urls:
            print(f"  Downloading {filename} from {url}")
            success = download_file(url, dataset_folder, filename)
            if success:
                print(f"  ✓ Successfully downloaded {filename}")
            else:
                print(f"  ✗ Failed to download {filename}")

if __name__ == "__main__":
    main()