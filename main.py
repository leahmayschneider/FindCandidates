from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from civic_info_api import CivicInfoAPI
from candidate_matcher import CandidateMatcher
import pandas as pd
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/fetch", response_class=HTMLResponse)
async def fetch(request: Request, address: str = Form(...)):
    endorsed_candidates_path = 'cleaned_wfp_candidates.xlsx'

    api = CivicInfoAPI()
    df, normalized_state = api.fetch_data(address)

    matcher = CandidateMatcher(endorsed_candidates_path)
    df = matcher.mark_endorsed_candidates(df, normalized_state)

    # Capture print statements
    log_output = matcher.get_output()

    # Define the columns to be included in the CSV
    columns_to_include = [
        "Division Name","Office Name","Levels","Roles","Official Name","Party","Endorsee"
    ]

    # Ensure only the specified columns are included in the output CSV
    df_to_export = df[columns_to_include]

    # Use /tmp directory for writable filesystem
    csv_file_path = '/tmp/representatives_info_with_endorsement.csv'
    df_to_export.to_csv(csv_file_path, index=False)

    return templates.TemplateResponse(
        "results.html", {
            "request": request,
            "log_output": log_output,
            "csv_link": "/download_csv"
        })

@app.get("/download_csv")
async def download_csv():
    csv_file_path = '/tmp/representatives_info_with_endorsement.csv'
    return FileResponse(csv_file_path, filename="representatives_info_with_endorsement.csv")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
