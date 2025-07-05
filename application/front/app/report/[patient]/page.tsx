"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";

export default function ReportPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const patientId = params.patient as string;
  const clientName = searchParams.get('clientName') || '';
  const [reportHtml, setReportHtml] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    // Load the report HTML from the server
    const loadReport = async () => {
      try {
        const response = await fetch('/report/report.html');
        if (response.ok) {
          const html = await response.text();
          setReportHtml(html);
        } else {
          setReportHtml('<p>Error loading report</p>');
        }
      } catch (error) {
        console.error('Error loading report:', error);
        setReportHtml('<p>Error loading report</p>');
      } finally {
        setLoading(false);
      }
    };

    loadReport();
  }, []);

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      // Create a link to download the HTML file as PDF
      // You might want to implement a backend endpoint that converts HTML to PDF
      const link = document.createElement("a");
      link.href = "/report/report.html";
      link.download = `${clientName}_report.html`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading PDF:', error);
    } finally {
      setDownloading(false);
    }
  };

  const handleBackToHome = () => {
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-xl flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-700 font-medium">Loading report...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={handleBackToHome}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors shadow-md"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Home
            </button>
            <h1 className="text-4xl font-bold text-gray-800">
              Medical Report - {clientName}
            </h1>
          </div>
          
          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleDownloadPDF}
              disabled={downloading}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-md disabled:opacity-50"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {downloading ? 'Downloading...' : 'Download as PDF'}
            </button>
            <Link
              href={`/chat/${patientId}?clientName=${encodeURIComponent(clientName)}`}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-md"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Ask MedGemma
            </Link>
          </div>
        </div>

        {/* Report Content */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">Patient Report</h2>
            
            {/* Report HTML Container */}
            <div 
              className="report-container border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-[600px] overflow-auto"
              dangerouslySetInnerHTML={{ __html: reportHtml }}
              style={{ 
                maxHeight: '800px',
                fontFamily: 'Arial, sans-serif',
                lineHeight: '1.6'
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
