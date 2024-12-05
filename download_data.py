import os
import re
import requests
from pathlib import Path
from typing import List, Tuple

def get_r_function_content(owner: str, repo: str, function_num: int) -> str:
    """Fetch the content of an R function file from GitHub."""
    padded_num = str(function_num).zfill(4)
    filename = f"data{padded_num}.R"
    
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/R/data/{filename}"
    response = requests.get(url)
    if response.status_code == 404:
        return None
    return response.text

def extract_download_info(r_content: str) -> List[Tuple[str, str]]:
    """Extract download URLs and their associated filenames from R function content."""
    if not r_content:
        return []
    
    downloads = []
    
    # First, find all variable assignments containing URLs
    # This pattern looks for variable assignments with URLs in them
    url_vars_pattern = r"(\w+)\s*<-\s*c\((.*?)\)"
    url_vars_matches = re.finditer(url_vars_pattern, r_content, re.DOTALL)
    
    url_vars = {}
    for match in url_vars_matches:
        var_name = match.group(1)
        # Extract URLs from the c(...) content
        urls = re.findall(r"['\"]((https?://|ftp://)[^'\"]+)['\"]", match.group(2))
        if urls:
            url_vars[var_name] = [url[0] for url in urls]  # url[0] because re.findall returns tuples for groups
    
    # Now find download.file calls and match them with the URLs
    download_pattern = r"download\.file\((.*?)\[(\d+)\].*?destfile\s*=\s*.*?['\"](.*?)['\"]"
    download_matches = re.finditer(download_pattern, r_content, re.DOTALL)
    
    for match in download_matches:
        var_name = match.group(1).strip()
        index = int(match.group(2)) - 1  # R uses 1-based indexing
        filename = os.path.basename(match.group(3).replace("paste0(folder, '", "").replace("')", ""))
        
        if var_name in url_vars and index < len(url_vars[var_name]):
            downloads.append((url_vars[var_name][index], filename))
    
    # Also look for direct URL downloads (not using variables)
    direct_pattern = r"download\.file\(['\"](https?://[^'\"]+)['\"]"
    direct_matches = re.finditer(direct_pattern, r_content, re.DOTALL)
    
    for match in direct_matches:
        url = match.group(1)
        # Look for the corresponding destfile
        destfile_pattern = f"download\.file\(['\"]({re.escape(url)})['\"].*?destfile\s*=\s*.*?['\"](.*?)['\"]"
        destfile_match = re.search(destfile_pattern, r_content, re.DOTALL)
        if destfile_match:
            filename = os.path.basename(destfile_match.group(2).replace("paste0(folder, '", "").replace("')", ""))
            downloads.append((url, filename))
    
    return downloads

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
    base_folder = Path("downloads")
    
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
        downloads = extract_download_info(r_content)
        if not downloads:
            print(f"No download URLs found in data{str(i).zfill(4)}.R")
            continue
            
        print(f"\nProcessing data{str(i).zfill(4)}:")
        for url, filename in downloads:
            print(f"  Downloading {filename} from {url}")
            success = download_file(url, dataset_folder, filename)
            if success:
                print(f"  ✓ Successfully downloaded {filename}")
            else:
                print(f"  ✗ Failed to download {filename}")

if __name__ == "__main__":
    main()