from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from pdf2image import convert_from_bytes

# Instância da aplicação (DEVE vir antes dos decoradores)
app = FastAPI(title="PDF OCR API")

# Middleware CORS
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
        # 1. Converte as páginas do PDF em imagens PIL (DPI 150 para poupar RAM)
        images = convert_from_bytes(pdf_bytes, dpi=150)
        
        if not images:
            raise HTTPException(status_code=400, detail="Não foi possível extrair páginas do PDF.")

        # 2. Processa o OCR das imagens e gera os bytes do PDF pesquisável
        pdf_final_bytes = pytesseract.image_to_pdf_or_hocr(images, lang=lang, extension='pdf')

        # 3. Retorna os bytes diretamente
        return Response(
            content=pdf_final_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ocr_{file.filename}"}
        )
    except Exception as e:
        print(f"Erro no OCR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")
