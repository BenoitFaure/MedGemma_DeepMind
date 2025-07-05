"use client";

import { useState } from "react";
import Link from "next/link";

interface Patient {
  id: string;
  name: string;
}

const PATIENTS: Patient[] = [
  { id: "alice", name: "Alice" },
  { id: "bob", name: "Bob" },
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-gray-800">ARIA Monitoring</h1>
          <button 
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-md"
            onClick={() => {}}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Patient
          </button>
        </div>

        {/* Patient List */}
        <div className="space-y-4">
          {PATIENTS.map((patient) => (
            <div key={patient.id} className="bg-white rounded-xl shadow-md overflow-hidden">
              <div 
                className="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => togglePatient(patient.id)}
              >
                <h2 className="text-xl font-semibold text-gray-800">{patient.name}</h2>
                <svg 
                  className={`w-6 h-6 text-gray-500 transform transition-transform ${
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
                <div className="px-6 pb-6 border-t border-gray-100">
                  <div className="flex flex-col sm:flex-row gap-3 mt-4">
                    <button
                      onClick={() => handleViewMRI(patient.name)}
                      className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-center font-medium"
                    >
                      Visualize MRI
                    </button>
                    <button
                      onClick={() => handleViewReport(patient.name, patient.id)}
                      className="flex-1 px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-center font-medium"
                    >
                      View Report
                    </button>
                    <Link 
                      href={`/chat/${patient.id}`}
                      className="flex-1 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-center font-medium"
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-xl shadow-xl flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-700 font-medium">
              {loading === "mri" ? "Processing MRI..." : "Generating report..."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
