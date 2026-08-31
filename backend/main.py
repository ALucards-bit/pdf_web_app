from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from pdf2image import convert_from_bytes

app = FastAPI(title="PDF OCR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "PDF OCR Backend"}

@app.post("/api/ocr")
async def process_ocr(file: UploadFile = File(...), lang: str = Form("por")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    
    try:
        # DPI em 120 para garantir que não vai estourar a memória do Render
        images = convert_from_bytes(pdf_bytes, dpi=120)
        
        if not images:
            raise HTTPException(status_code=400, detail="O PDF parece estar vazio ou corrompido.")

        # Limite de páginas por requisição para a camada gratuita do Render
        if len(images) > 10:
            raise HTTPException(status_code=400, detail="Envie um PDF com no máximo 10 páginas para este ambiente.")

        # Processamento direto das imagens com pytesseract
        pdf_final_bytes = pytesseract.image_to_pdf_or_hocr(images, lang=lang, extension='pdf')

        return Response(
            content=pdf_final_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ocr_{file.filename}"}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento OCR: {str(e)}")
