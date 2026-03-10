# Fatura2Excel - Turkish Invoice PDF to Excel Converter

A B2B SaaS application that converts Turkish GİB E-Arşiv PDF invoices to structured Excel files with near 100% accuracy.

## Tech Stack

- **Frontend**: Next.js 13 (App Router), Tailwind CSS, Lucide Icons
- **Backend**: Python, FastAPI
- **PDF Processing**: pdfplumber, pandas, openpyxl

## Features

- Drag-and-drop multiple PDF uploads
- Automatic extraction of 7 critical invoice fields:
  - Fatura Tarihi (Invoice Date)
  - Fatura No (Invoice Number)
  - VKN/TCKN (Tax ID)
  - Müşteri Adı (Customer Name)
  - Matrah (Subtotal)
  - KDV (Tax Amount)
  - Toplam (Grand Total)
- Real-time processing progress
- Instant Excel file download
- Beautiful, production-ready UI

## Installation & Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- pip

### Backend Setup

1. Navigate to the backend folder:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the FastAPI server:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. In the project root folder, install dependencies:
```bash
npm install
```

2. Start the Next.js development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Drag and drop your Turkish GİB E-Arşiv PDF invoices or click to select files
3. Click "Excel'e Dönüştür" (Convert to Excel)
4. The Excel file will automatically download as "Fatura_Raporu.xlsx"

## API Endpoints

### `GET /`
Health check endpoint

**Response:**
```json
{
  "message": "Fatura2Excel API is running",
  "status": "healthy",
  "version": "1.0.0"
}
```

### `POST /api/convert`
Convert PDF invoices to Excel

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: Multiple PDF files

**Response:**
- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Body: Excel file (binary)

## Project Structure

```
├── app/                    # Next.js app directory
│   ├── page.tsx           # Main upload page
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── backend/               # Python FastAPI backend
│   ├── main.py           # FastAPI server
│   ├── parser.py         # PDF parsing logic
│   └── requirements.txt  # Python dependencies
├── components/           # React components
│   └── ui/              # shadcn/ui components
└── README.md            # This file
```

## Build for Production

### Frontend
```bash
npm run build
npm start
```

### Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## License

This project is proprietary software.
