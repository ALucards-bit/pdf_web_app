from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from pdf2image import convert_from_bytes
import pymupdf as fitz

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
        # 1. Converte o PDF em lista de imagens PIL
        images = convert_from_bytes(pdf_bytes, dpi=120)
        
        if not images:
            raise HTTPException(status_code=400, detail="O PDF está vazio ou corrompido.")

        if len(images) > 10:
            raise HTTPException(status_code=400, detail="Envie um PDF com no máximo 10 páginas.")

        # 2. Cria o documento PDF final acumulador
        pdf_pesquisavel = fitz.open()

        for img in images:
            # Converte imagem por imagem para PDF em bytes via Tesseract
            pdf_page_bytes = pytesseract.image_to_pdf_or_hocr(img, lang=lang, extension='pdf')
            
            # Abre os bytes da página e insere no documento final
            page_doc = fitz.open("pdf", pdf_page_bytes)
            pdf_pesquisavel.insert_pdf(page_doc)
            page_doc.close()

        # 3. Extrai os bytes finais
        output_pdf_bytes = pdf_pesquisavel.tobytes()
        pdf_pesquisavel.close()

        return Response(
            content=output_pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ocr_{file.filename}"}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento OCR: {str(e)}")
