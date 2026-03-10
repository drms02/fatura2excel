from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import pandas as pd
from io import BytesIO
from invoice_parser import process_multiple_pdfs
import os

app = FastAPI(title="Fatura2Excel API", version="1.0.0")

frontend_url = os.getenv("FRONTEND_URL", "")

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Fatura2Excel API is running",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.post("/api/convert")
async def convert_pdfs_to_excel(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    pdf_files = []
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Only PDF files are allowed."
            )
        content = await file.read()
        pdf_files.append((file.filename, content))

    try:
        results = process_multiple_pdfs(pdf_files)

        if not results:
            raise HTTPException(status_code=500, detail="Failed to process PDF files")

        df = pd.DataFrame(results)

        column_order = [
            "Dosya Adı",
            "Fatura Tarihi",
            "Fatura No",
            "VKN/TCKN",
            "Müşteri Adı",
            "Matrah",
            "KDV",
            "Toplam"
        ]
        df = df[column_order]

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Faturalar')
            worksheet = writer.sheets['Faturalar']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_length

        excel_buffer.seek(0)

        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=Fatura_Raporu.xlsx"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
