'use client';

import { useState, useCallback } from 'react';
import { Upload, FileText, Download, CircleCheck as CheckCircle, Circle as XCircle, Loader as Loader2, FileSpreadsheet, Paperclip } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface UploadedFile {
  file: File;
  id: string;
}

export default function Home() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [existingExcel, setExistingExcel] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.name.toLowerCase().endsWith('.pdf') || file.name.toLowerCase().endsWith('.xml')
    );
    const newFiles = droppedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9)
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files).filter(
        file => file.name.toLowerCase().endsWith('.pdf') || file.name.toLowerCase().endsWith('.xml')
      );
      const newFiles = selectedFiles.map(file => ({
        file,
        id: Math.random().toString(36).substr(2, 9)
      }));
      setFiles(prev => [...prev, ...newFiles]);
    }
  }, []);

  const handleExcelSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setExistingExcel(e.target.files[0]);
    }
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  const handleConvert = async () => {
    if (files.length === 0) return;

    setIsProcessing(true);
    setStatus('processing');
    setProgress(0);
    setErrorMessage('');

    try {
      const formData = new FormData();
      files.forEach(({ file }) => formData.append('files', file));
      if (existingExcel) formData.append('existing_excel', existingExcel);

      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) { clearInterval(progressInterval); return 90; }
          return prev + 10;
        });
      }, 300);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/convert`, {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'İşlem başarısız');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'Fatura_Raporu.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setStatus('success');
      setTimeout(() => {
        setFiles([]);
        setExistingExcel(null);
        setStatus('idle');
        setProgress(0);
      }, 3000);

    } catch (error) {
      setStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Bir hata oluştu');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-900 rounded-2xl mb-4">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-slate-900 mb-3">Fatura2Excel</h1>
            <p className="text-lg text-slate-600">
              GİB E-Arşiv faturalarınızı saniyeler içinde Excel'e dönüştürün
            </p>
          </div>

          <Card className="p-8 shadow-xl border-0 bg-white">

            {/* Ana yükleme alanı: PDF + XML */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-xl p-12 transition-all duration-200 ${
                isDragging ? 'border-slate-900 bg-slate-50' : 'border-slate-300 hover:border-slate-400'
              }`}
            >
              <input
                type="file"
                id="file-upload"
                multiple
                accept=".pdf,.xml"
                onChange={handleFileSelect}
                className="hidden"
              />
              <div className="text-center">
                <Upload className={`mx-auto h-12 w-12 mb-4 ${isDragging ? 'text-slate-900' : 'text-slate-400'}`} />
                <label htmlFor="file-upload" className="cursor-pointer text-slate-900 hover:text-slate-700 font-semibold">
                  PDF veya XML dosyalarınızı seçin
                </label>
                <span className="text-slate-600"> veya sürükleyip bırakın</span>
                <p className="text-sm text-slate-500 mt-2">
                  GİB e-Arşiv PDF ve e-Fatura XML dosyaları desteklenmektedir
                </p>
              </div>
            </div>

            {/* Seçilen fatura dosyaları */}
            {files.length > 0 && (
              <div className="mt-6 space-y-2">
                <h3 className="font-semibold text-slate-900 mb-3">
                  Fatura Dosyaları ({files.length})
                </h3>
                {files.map(({ file, id }) => (
                  <div key={id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-slate-600" />
                      <span className="text-sm text-slate-700">{file.name}</span>
                      <span className="text-xs text-slate-500">({(file.size / 1024).toFixed(1)} KB)</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        file.name.toLowerCase().endsWith('.xml')
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-orange-100 text-orange-700'
                      }`}>
                        {file.name.toLowerCase().endsWith('.xml') ? 'XML' : 'PDF'}
                      </span>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => removeFile(id)} disabled={isProcessing}>
                      <XCircle className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Mevcut Excel yükleme (opsiyonel) */}
            <div className="mt-6">
              <div className="flex items-center gap-2 mb-2">
                <FileSpreadsheet className="h-4 w-4 text-slate-500" />
                <span className="text-sm font-medium text-slate-700">
                  Mevcut Excel'e ekle <span className="text-slate-400 font-normal">(opsiyonel)</span>
                </span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="file"
                  id="excel-upload"
                  accept=".xlsx"
                  onChange={handleExcelSelect}
                  className="hidden"
                />
                <label
                  htmlFor="excel-upload"
                  className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:border-slate-400 hover:bg-slate-50 transition-all"
                >
                  <Paperclip className="h-4 w-4" />
                  {existingExcel ? existingExcel.name : 'Excel dosyası seç (.xlsx)'}
                </label>
                {existingExcel && (
                  <button
                    onClick={() => setExistingExcel(null)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    Kaldır
                  </button>
                )}
              </div>
              {existingExcel && (
                <p className="text-xs text-slate-500 mt-1">
                  Yeni faturalar bu Excel'e eklenecek, tekrar eden fatura numaraları atlanacak.
                </p>
              )}
            </div>

            {/* Progress bar */}
            {isProcessing && (
              <div className="mt-6 space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-700 font-medium">İşleniyor...</span>
                  <span className="text-slate-600">{progress}%</span>
                </div>
                <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full bg-slate-900 transition-all duration-300" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}

            {status === 'success' && (
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-green-800 font-medium">Excel dosyanız başarıyla indirildi!</span>
              </div>
            )}

            {status === 'error' && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3">
                <XCircle className="h-5 w-5 text-red-600" />
                <div className="flex-1">
                  <p className="text-red-800 font-medium">Hata oluştu</p>
                  <p className="text-sm text-red-600 mt-1">{errorMessage}</p>
                </div>
              </div>
            )}

            <div className="mt-8 flex justify-center">
              <Button
                onClick={handleConvert}
                disabled={files.length === 0 || isProcessing}
                size="lg"
                className="px-8 bg-slate-900 hover:bg-slate-800"
              >
                {isProcessing ? (
                  <><Loader2 className="mr-2 h-5 w-5 animate-spin" />İşleniyor...</>
                ) : (
                  <><Download className="mr-2 h-5 w-5" />Excel'e Dönüştür</>
                )}
              </Button>
            </div>
          </Card>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 text-center border-0 shadow-md">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Upload className="h-6 w-6 text-slate-700" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Kolay Yükleme</h3>
              <p className="text-sm text-slate-600">PDF ve XML formatında toplu fatura yükleyin</p>
            </Card>
            <Card className="p-6 text-center border-0 shadow-md">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <FileText className="h-6 w-6 text-slate-700" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Otomatik Okuma</h3>
              <p className="text-sm text-slate-600">GİB formatındaki tüm fatura bilgileri otomatik çıkarılır</p>
            </Card>
            <Card className="p-6 text-center border-0 shadow-md">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Download className="h-6 w-6 text-slate-700" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Anında İndirin</h3>
              <p className="text-sm text-slate-600">Düzenli Excel formatında raporunuzu hemen alın</p>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
