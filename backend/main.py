from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import pymupdf as fitz
import pytesseract
from pdf2image import convert_from_bytes
import io

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
        # DPI reduzido para 150 para economizar memória RAM no Render
        images = convert_from_bytes(pdf_bytes, dpi=150)
        pdf_pesquisavel = fitz.open()

        for img in images:
            # Gera os bytes do PDF pesquisável diretamente com o pytesseract
            pdf_page_bytes = pytesseract.image_to_pdf_or_hocr(img, lang=lang, extension='pdf')
            
            # Abre os bytes da página com PyMuPDF e insere no documento final
            page_doc = fitz.open("pdf", pdf_page_bytes)
            pdf_pesquisavel.insert_pdf(page_doc)
            page_doc.close()

        # Extrai os bytes finais do PDF acumulado
        output_pdf_bytes = pdf_pesquisavel.tobytes()
        pdf_pesquisavel.close()

        if not output_pdf_bytes:
            raise HTTPException(status_code=500, detail="Nenhum conteúdo PDF foi gerado.")

        return Response(
            content=output_pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ocr_{file.filename}"}
        )
    except Exception as e:
        print(f"Erro detalhado no servidor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")
