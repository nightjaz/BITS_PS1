import sys
import requests
from io import BytesIO
from PyPDF2 import PdfMerger
import os

# Function to download a PDF from a URL into memory
def download_pdf(url):
    print(f"Downloading: {url}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

# Function to merge multiple PDFs from URLs
def merge_pdfs_from_urls(urls, output_path):
    merger = PdfMerger()
    downloaded_count = 0
    for url in urls:
        pdf_file = download_pdf(url)
        if pdf_file:
            merger.append(pdf_file)
            downloaded_count += 1
        else:
            print(f"Skipping {url} due to download error.")

    if downloaded_count == 0:
        print("No PDFs were successfully downloaded. Merging aborted.")
        merger.close()
        return

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Write the merged PDF to the specified output path
    with open(output_path, "wb") as f_out:
        merger.write(f_out)
    merger.close()
    print(f"Successfully merged {downloaded_count} PDFs into {output_path}")

# URLs for Physics Class 12 parts
# leph102.pdf to leph108.pdf (Parts 1, Chapters 2-8)
# leph201.pdf to leph206.pdf (Parts 2, Chapters 1-6)
# Note: NCERT's naming convention for chapters might vary slightly, double-check if any parts are missing
urls = [
    f"https://ncert.nic.in/textbook/pdf/leph10{i}.pdf" for i in range(2, 9)
] + [
    f"https://ncert.nic.in/textbook/pdf/leph20{i}.pdf" for i in range(1, 7)
]

# Define the output path in the /content/ncert_books directory
output_pdf_filename = "physicsClass12Merged.pdf"
output_directory = "/content/ncert_books"
output_full_path = os.path.join(output_directory, output_pdf_filename)

# Execute the merge
merge_pdfs_from_urls(urls, output_full_path)

print(f"Merging process completed. Check '{output_full_path}'")
