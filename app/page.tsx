'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth, SignInButton, UserButton } from '@clerk/nextjs';
import {
  Upload, FileText, Download, CircleCheck as CheckCircle,
  Circle as XCircle, Loader as Loader2, FileSpreadsheet, Paperclip, Coins
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface UploadedFile {
  file: File;
  id: string;
}

export default function Home() {
  const { isLoaded, isSignedIn, getToken } = useAuth();

  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [existingExcel, setExistingExcel] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  // Auth & credits
  const [credits, setCredits] = useState<number | null>(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const paymentLink = process.env.NEXT_PUBLIC_PAYMENT_LINK || '#';

  // ——— Kredi çekme ———
  const fetchCredits = useCallback(async () => {
    try {
      const token = await getToken();
      const resp = await fetch(`${apiUrl}/api/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const data = await resp.json();
        setCredits(data.credits);
      }
    } catch {
      // sessiz hata
    }
  }, [getToken, apiUrl]);

  useEffect(() => {
    if (isSignedIn) {
      fetchCredits();
    } else {
      setCredits(null);
    }
  }, [isSignedIn, fetchCredits]);

  // ——— Dosya işlemleri ———
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
    setFiles(prev => [...prev, ...droppedFiles.map(file => ({ file, id: Math.random().toString(36).substr(2, 9) }))]);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files).filter(
        file => file.name.toLowerCase().endsWith('.pdf') || file.name.toLowerCase().endsWith('.xml')
      );
      setFiles(prev => [...prev, ...selected.map(file => ({ file, id: Math.random().toString(36).substr(2, 9) }))]);
    }
  }, []);

  const handleExcelSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setExistingExcel(e.target.files[0]);
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  // ——— Dönüştürme ———
  const handleConvert = async () => {
    if (files.length === 0) return;

    // Kredi kontrolü (frontend tarafı)
    if (credits !== null && credits < files.length) {
      setShowPaymentModal(true);
      return;
    }

    setIsProcessing(true);
    setStatus('processing');
    setProgress(0);
    setErrorMessage('');

    try {
      const token = await getToken();
      const formData = new FormData();
      files.forEach(({ file }) => formData.append('files', file));
      if (existingExcel) formData.append('existing_excel', existingExcel);

      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) { clearInterval(progressInterval); return 90; }
          return prev + 10;
        });
      }, 300);

      const response = await fetch(`${apiUrl}/api/convert`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (response.status === 401) {
        setStatus('error');
        setErrorMessage('Oturum süresi dolmuş. Lütfen yeniden giriş yapın.');
        return;
      }

      if (response.status === 402) {
        setShowPaymentModal(true);
        setStatus('idle');
        return;
      }

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

      // Kalan krediyi güncelle
      await fetchCredits();

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

  // ——— Convert butonu ———
  const renderConvertButton = () => {
    if (!isLoaded) return null;

    if (!isSignedIn) {
      return (
        <SignInButton mode="modal">
          <Button size="lg" className="px-8 bg-slate-900 hover:bg-slate-800 cursor-pointer">
            <span className="mr-2">🔑</span>
            Google ile Giriş Yap
          </Button>
        </SignInButton>
      );
    }

    if (credits !== null && files.length > 0 && credits < files.length) {
      return (
        <Button
          onClick={() => setShowPaymentModal(true)}
          size="lg"
          className="px-8 bg-amber-600 hover:bg-amber-700"
        >
          <Coins className="mr-2 h-5 w-5" />
          Yetersiz Kredi — Satın Al
        </Button>
      );
    }

    return (
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
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">

          {/* Header */}
          <div className="flex items-start justify-between mb-12">
            <div className="text-center flex-1">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-900 rounded-2xl mb-4">
                <FileText className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 mb-3">Fatura2Excel</h1>
              <p className="text-lg text-slate-600">
                GİB E-Arşiv faturalarınızı saniyeler içinde Excel&apos;e dönüştürün
              </p>
            </div>

            {/* Kredi badge + kullanıcı */}
            <div className="flex items-center gap-3 pt-2 min-w-[140px] justify-end">
              {isSignedIn && credits !== null && (
                <div className="flex items-center gap-1.5 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-full">
                  <Coins className="h-4 w-4 text-amber-600" />
                  <span className="text-sm font-semibold text-amber-700">{credits} kredi</span>
                </div>
              )}
              {isSignedIn && <UserButton afterSignOutUrl="/" />}
            </div>
          </div>

          <Card className="p-8 shadow-xl border-0 bg-white">

            {/* Ana yükleme alanı */}
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
                <p className="text-xs text-slate-400 mt-1">
                  Her dosya için 1 kredi kullanılır
                </p>
              </div>
            </div>

            {/* Seçilen dosyalar */}
            {files.length > 0 && (
              <div className="mt-6 space-y-2">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-900">
                    Fatura Dosyaları ({files.length})
                  </h3>
                  {isSignedIn && credits !== null && (
                    <span className={`text-sm font-medium px-2 py-1 rounded-full ${
                      credits >= files.length
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {files.length} kredi kullanılacak (kalan: {credits})
                    </span>
                  )}
                </div>
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

            {/* Mevcut Excel (opsiyonel) */}
            <div className="mt-6">
              <div className="flex items-center gap-2 mb-2">
                <FileSpreadsheet className="h-4 w-4 text-slate-500" />
                <span className="text-sm font-medium text-slate-700">
                  Mevcut Excel&apos;e ekle <span className="text-slate-400 font-normal">(opsiyonel)</span>
                </span>
              </div>
              <div className="flex items-center gap-3">
                <input type="file" id="excel-upload" accept=".xlsx" onChange={handleExcelSelect} className="hidden" />
                <label
                  htmlFor="excel-upload"
                  className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:border-slate-400 hover:bg-slate-50 transition-all"
                >
                  <Paperclip className="h-4 w-4" />
                  {existingExcel ? existingExcel.name : 'Excel dosyası seç (.xlsx)'}
                </label>
                {existingExcel && (
                  <button onClick={() => setExistingExcel(null)} className="text-xs text-red-500 hover:text-red-700">
                    Kaldır
                  </button>
                )}
              </div>
              {existingExcel && (
                <p className="text-xs text-slate-500 mt-1">
                  Yeni faturalar bu Excel&apos;e eklenecek, tekrar eden fatura numaraları atlanacak.
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
                <div>
                  <span className="text-green-800 font-medium">Excel dosyanız başarıyla indirildi!</span>
                  {credits !== null && (
                    <p className="text-sm text-green-600 mt-0.5">Kalan krediniz: {credits}</p>
                  )}
                </div>
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

            {/* Giriş yapılmamış uyarı */}
            {isLoaded && !isSignedIn && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-center">
                <p className="text-blue-700 text-sm">
                  Dönüştürmek için Google ile giriş yapmanız gerekiyor.{' '}
                  <span className="font-semibold">5 ücretsiz dönüştürme</span> hakkı tanınacak.
                </p>
              </div>
            )}

            <div className="mt-8 flex justify-center">
              {renderConvertButton()}
            </div>
          </Card>

          {/* Özellik kartları */}
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

      {/* ——— Ödeme Modalı ——— */}
      {showPaymentModal && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
          onClick={() => setShowPaymentModal(false)}
        >
          <div
            className="bg-white rounded-2xl p-8 max-w-sm w-full shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="text-center">
              <div className="text-5xl mb-4">🎉</div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Ücretsiz krediniz bitti!</h2>
              <p className="text-slate-600 mb-6 text-sm">
                Aylık SMMM paketine geçerek dönüştürmeye devam edin.
              </p>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 mb-6 text-left">
                <div className="font-semibold text-slate-900 text-lg">Aylık SMMM Paketi</div>
                <div className="text-sm text-slate-500 mt-1">50 dönüştürme hakkı / ay</div>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-slate-900">299</span>
                  <span className="text-slate-500">₺ / ay</span>
                </div>
                <ul className="mt-3 space-y-1 text-sm text-slate-600">
                  <li>✅ 50 toplu fatura dönüştürme</li>
                  <li>✅ PDF + XML desteği</li>
                  <li>✅ Excel merge özelliği</li>
                  <li>✅ Öncelikli destek</li>
                </ul>
              </div>
              <a
                href={paymentLink}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full bg-slate-900 text-white py-3 px-6 rounded-xl font-semibold hover:bg-slate-700 transition-colors text-center"
              >
                Şimdi Satın Al →
              </a>
              <button
                onClick={() => setShowPaymentModal(false)}
                className="mt-4 text-sm text-slate-400 hover:text-slate-600 transition-colors"
              >
                Şimdi değil
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
