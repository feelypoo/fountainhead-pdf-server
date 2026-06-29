from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import traceback

from generate_pdf import generate

app = FastAPI(title="Fountainhead PDF Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class WineBTG(BaseModel):
    vintage: Optional[str] = ""
    producer: str
    cuvee: str
    grapes: str
    region: str
    country: str
    btg_price: str


class WineBTB(BaseModel):
    vintage: Optional[str] = ""
    producer: str
    cuvee: str
    grapes: str
    region: str
    country: str
    btl_price: str
    note: Optional[str] = ""


class Section(BaseModel):
    heading: str
    wines: list


class FixedSection(BaseModel):
    heading: str
    items: list


class MenuData(BaseModel):
    btg_sections: list[Section] = []
    btb_sections: list[Section] = []
    fixed_sections: Optional[list[FixedSection]] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate_pdf(data: MenuData):
    try:
        pdf_bytes = generate(data.model_dump())
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="fountainhead_menu.pdf"'},
        )
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())
