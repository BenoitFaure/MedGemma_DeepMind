"use client";

import { useState } from "react";
import Link from "next/link";

interface Patient {
  id: string;
  name: string;
  dateOfBirth: string;
  age: number;
  treatmentStartDate: string;
  newMRIAvailableDate?: string; // Optional property for new MRI availability
}

const PATIENTS: Patient[] = [
  { 
    id: "alice", 
    name: "Alice", 
    dateOfBirth: "1947-03-15",
    age: 78,
    treatmentStartDate: "2024-01-15",
    newMRIAvailableDate: "2025-04-18"
  },
  { 
    id: "bob", 
    name: "Bob",
    dateOfBirth: "1968-08-22",
    age: 56,
    treatmentStartDate: "2023-11-08"
  },
];

export default function Home() {
  const [expandedPatient, setExpandedPatient] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  const togglePatient = (patientId: string) => {
    setExpandedPatient(expandedPatient === patientId ? null : patientId);
  };

  const handleViewReport = async (patientName: string, patientId: string) => {
    setLoading("report");
    try {
      const response = await fetch("http://localhost:8000/report", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ client_name: patientName }),
      });
      
      if (response.ok) {
        // Navigate to the report page
        window.location.href = `/report/${patientId}?clientName=${encodeURIComponent(patientName)}`;
      }
    } catch (error) {
      console.error("Error generating report:", error);
    } finally {
      setLoading(null);
    }
  };

  const handleViewMRI = async (patientName: string) => {
    setLoading("mri");
    try {
      const response = await fetch("http://localhost:8000/seg", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        window.location.href = `/mri/${patientName.toLowerCase().replace(" ", "-")}`;
      }
    } catch (error) {
      console.error("Error processing MRI:", error);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#181028] via-[#1a1333] to-black">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-5xl font-extrabold text-white tracking-tight drop-shadow-lg" style={{ letterSpacing: '0.03em' }}>Gemm<span className="text-[#A259F7]">ARIA</span></h1>
          <button 
            className="flex items-center gap-2 px-5 py-2 bg-[#3B1E6D] text-white rounded-2xl hover:bg-[#A259F7] transition-colors shadow-lg border border-[#A259F7]/40 font-semibold text-lg"
            onClick={() => {}}
            style={{ boxShadow: '0 0 12px #A259F7aa' }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Patient
          </button>
        </div>

        {/* Patient List */}
        <div className="space-y-6">
          {PATIENTS.map((patient) => (
            <div key={patient.id} className="bg-[#1a1333]/80 rounded-3xl shadow-2xl overflow-hidden border border-[#A259F7]/30 backdrop-blur-md">
              <div 
                className="flex items-center justify-between p-8 cursor-pointer hover:bg-[#2a1a4d]/60 transition-colors"
                onClick={() => togglePatient(patient.id)}
              >
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                    {patient.name}
                    {/* Badge pour Alice si newMRIAvailableDate existe */}
                    {patient.newMRIAvailableDate && (
                      <span className="ml-2 px-3 py-1 bg-gradient-to-r from-[#A259F7] to-[#3B1E6D] text-white text-xs rounded-full font-semibold border border-[#A259F7] shadow-md">
                        New MRI · {new Date(patient.newMRIAvailableDate).toLocaleDateString()}
                      </span>
                    )}
                  </h2>
                  <div className="flex flex-wrap gap-8 text-base text-[#E0D7F7]">
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-[#A259F7]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span><strong>DOB:</strong> {new Date(patient.dateOfBirth).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-[#A259F7]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span><strong>Age:</strong> {patient.age} years</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-[#A259F7]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                      <span><strong>Treatment Start:</strong> {new Date(patient.treatmentStartDate).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <svg 
                  className={`w-7 h-7 text-[#A259F7] transform transition-transform ${
                    expandedPatient === patient.id ? 'rotate-90' : ''
                  }`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
              
              {expandedPatient === patient.id && (
                <div className="px-8 pb-8 border-t border-[#A259F7]/20 bg-[#221a36]/60 backdrop-blur-md">
                  <div className="flex flex-col sm:flex-row gap-4 mt-6">
                    <button
                      onClick={() => handleViewMRI(patient.name)}
                      className="flex-1 px-5 py-3 bg-gradient-to-r from-[#3B1E6D] to-[#A259F7] text-white rounded-xl hover:from-[#A259F7] hover:to-[#3B1E6D] transition-colors text-center font-semibold shadow-lg border border-[#A259F7]/40"
                      style={{ boxShadow: '0 0 8px #A259F7aa' }}
                    >
                      Visualize MRI
                    </button>
                    <button
                      onClick={() => handleViewReport(patient.name, patient.id)}
                      className="flex-1 px-5 py-3 bg-gradient-to-r from-[#F76B1C] to-[#A259F7] text-white rounded-xl hover:from-[#A259F7] hover:to-[#F76B1C] transition-colors text-center font-semibold shadow-lg border border-[#A259F7]/40"
                      style={{ boxShadow: '0 0 8px #F76B1Caa' }}
                    >
                      View Report
                    </button>
                    <Link 
                      href={`/chat/${patient.id}`}
                      className="flex-1 px-5 py-3 bg-gradient-to-r from-[#A259F7] to-[#3B1E6D] text-white rounded-xl hover:from-[#3B1E6D] hover:to-[#A259F7] transition-colors text-center font-semibold shadow-lg border border-[#A259F7]/40"
                      style={{ boxShadow: '0 0 8px #A259F7aa' }}
                    >
                      Chat with MedGemma
                    </Link>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Loading Modal */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
          <div className="bg-[#181028] p-10 rounded-3xl shadow-2xl flex flex-col items-center border border-[#A259F7]/30">
            <div className="animate-spin rounded-full h-14 w-14 border-b-4 border-[#A259F7] mb-6"></div>
            <p className="text-white font-semibold text-lg">
              {loading === "mri" ? "Processing MRI..." : "Generating report..."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
