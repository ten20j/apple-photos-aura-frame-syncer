from fastapi import FastAPI, Request, Form, Path
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from .jobs import sync_photos_to_aura
from clients.apple_photos import list_all_person_names, get_sample_photos_for_person, list_albums
import glob

app = FastAPI()

# Ensure templates directory exists
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
os.makedirs(TEMPLATES_DIR, exist_ok=True)
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Serve static files from temp dirs for sample images
temp_sample_dirs = []

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, sync_status: str = None):
    albums = list_albums()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "sync_status": sync_status,
            "albums": albums
        }
    )

@app.post("/sync")
def manual_sync(request: Request, album_name: str = Form(None)):
    if album_name:
        success = sync_photos_to_aura(album_name=album_name)
        status = f"Sync completed successfully for album '{album_name}!" if success else f"Sync failed for album '{album_name}'."
    else:
        # Test mode with random photo
        success = sync_photos_to_aura()
        status = "Random photo sync completed successfully!" if success else "Sync failed."
    
    url = f"/?sync_status={status}"
    return RedirectResponse(url, status_code=303)

@app.get("/faces", response_class=HTMLResponse)
def faces(request: Request):
    person_names = list_all_person_names()
    return templates.TemplateResponse("faces.html", {"request": request, "person_names": person_names})

@app.get("/faces/{person_name}", response_class=HTMLResponse)
def face_samples(request: Request, person_name: str = Path(...)):
    sample_paths = get_sample_photos_for_person(person_name)
    # Register temp dir for static serving
    if sample_paths:
        temp_dir = os.path.dirname(sample_paths[0])
        if temp_dir not in temp_sample_dirs:
            app.mount(f"/samples/{os.path.basename(temp_dir)}", StaticFiles(directory=temp_dir), name=f"samples-{os.path.basename(temp_dir)}")
            temp_sample_dirs.append(temp_dir)
        # Convert to URLs for browser
        sample_urls = [f"/samples/{os.path.basename(temp_dir)}/{os.path.basename(p)}" for p in sample_paths]
    else:
        sample_urls = []
    return templates.TemplateResponse("face_samples.html", {"request": request, "person_name": person_name, "sample_urls": sample_urls}) 