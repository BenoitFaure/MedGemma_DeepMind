"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export default function MRIViewer({ params }: { params: { patient: string } }) {
  const patientName = params.patient.replace("-", " ");
  const [currentSlice, setCurrentSlice] = useState(77); // Middle slice (154/2)
  const [showSegmentation, setShowSegmentation] = useState(false);
  const [showProgression, setShowProgression] = useState(false);
  const [imagesLoaded, setImagesLoaded] = useState(true);

  const totalSlices = 154;
  const leftDate = "2025-03-24";
  const rightDate = "2025-04-18";

  // Format slice number with leading zeros
  const formatSliceNumber = (slice: number) => {
    return slice.toString().padStart(3, '0');
  };

  // Get image paths based on segmentation or progression toggle
  const getImagePaths = () => {
    const basePath = "/mri/";
    let leftFolder = "0";
    let rightFolder;
    if (showProgression) {
      rightFolder = "difference";
    } else if (showSegmentation) {
      leftFolder = "0.seg";
      rightFolder = "1.seg";
    } else {
      rightFolder = "1";
    }
    const sliceFile = `slice_${formatSliceNumber(currentSlice)}.jpg`;
    return {
      left: `${basePath}${leftFolder}/${sliceFile}`,
      right: `${basePath}${rightFolder}/${sliceFile}`
    };
  };

  const imagePaths = getImagePaths();

  useEffect(() => {
    // Preload some images around current slice for smoother navigation
    const preloadImages = () => {
      const range = 5; // Preload 5 slices before and after
      for (let i = Math.max(0, currentSlice - range); i <= Math.min(totalSlices - 1, currentSlice + range); i++) {
        // Preload left image
        let leftSrc = `/mri/0/slice_${formatSliceNumber(i)}.jpg`;
        let rightSrc;
        if (showProgression) {
          rightSrc = `/mri/difference/slice_${formatSliceNumber(i)}.jpg`;
        } else if (showSegmentation) {
          leftSrc = `/mri/0.seg/slice_${formatSliceNumber(i)}.jpg`;
          rightSrc = `/mri/1.seg/slice_${formatSliceNumber(i)}.jpg`;
        } else {
          rightSrc = `/mri/1/slice_${formatSliceNumber(i)}.jpg`;
        }
        const leftImg = new Image();
        leftImg.src = leftSrc;
        const rightImg = new Image();
        rightImg.src = rightSrc;
      }
    };

    preloadImages();
  }, [currentSlice, showSegmentation, showProgression]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#181028] via-[#1a1333] to-black">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-extrabold text-white tracking-tight drop-shadow-lg mb-2" style={{ letterSpacing: '0.03em' }}>MRI <span className="text-[#A259F7]">Viewer</span></h1>
            <p className="text-[#E0D7F7]">Patient: {patientName}</p>
          </div>
          <Link 
            href="/"
            className="px-5 py-2 bg-gradient-to-r from-[#3B1E6D] to-[#A259F7] text-white rounded-2xl hover:from-[#A259F7] hover:to-[#3B1E6D] transition-colors shadow-lg border border-[#A259F7]/40 font-semibold text-lg"
            style={{ boxShadow: '0 0 8px #A259F7aa' }}
          >
            Back to Home
          </Link>
        </div>

        {/* Controls */}
        <div className="bg-[#1a1333]/80 rounded-3xl shadow-2xl p-8 mb-8 border border-[#A259F7]/30 backdrop-blur-md">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <span className="text-[#E0D7F7] font-medium">Slice: {currentSlice + 1} / {totalSlices}</span>
              <button
                onClick={() => {
                  setShowSegmentation(!showSegmentation);
                  if (!showSegmentation) setShowProgression(false);
                }}
                className={`px-4 py-2 rounded-xl font-semibold transition-colors border border-[#A259F7]/40 shadow-md ${
                  showSegmentation
                    ? "bg-gradient-to-r from-[#A259F7] to-[#3B1E6D] text-white"
                    : "bg-[#221a36] text-[#A259F7] hover:bg-[#2a1a4d]"
                }`}
                style={showSegmentation ? { boxShadow: '0 0 8px #A259F7aa' } : {}}
              >
                {showSegmentation ? "Hide Segmentation" : "Show Segmentation"}
              </button>
              <button
                onClick={() => {
                  setShowProgression(!showProgression);
                  if (!showProgression) setShowSegmentation(false);
                }}
                className={`px-4 py-2 rounded-xl font-semibold transition-colors border border-[#A259F7]/40 shadow-md ${
                  showProgression
                    ? "bg-gradient-to-r from-[#F76B1C] to-[#A259F7] text-white"
                    : "bg-[#221a36] text-[#F76B1C] hover:bg-[#2a1a4d]"
                }`}
                style={showProgression ? { boxShadow: '0 0 8px #F76B1Caa' } : {}}
              >
                {showProgression ? "Hide Progression" : "Show Progression"}
              </button>
            </div>
          </div>

          {/* Slice Slider */}
          <div className="w-full">
            <input
              type="range"
              min="0"
              max={totalSlices - 1}
              value={currentSlice}
              onChange={(e) => setCurrentSlice(parseInt(e.target.value))}
              className="w-full h-2 bg-[#2a1a4d] rounded-lg appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, #A259F7 0%, #A259F7 ${(currentSlice / (totalSlices - 1)) * 100}%, #221a36 ${(currentSlice / (totalSlices - 1)) * 100}%, #221a36 100%)`
              }}
            />
            <div className="flex justify-between text-sm text-[#A259F7] mt-2">
              <span>Slice 1</span>
              <span>Slice {totalSlices}</span>
            </div>
          </div>
        </div>

        {/* MRI Images */}
        <div className="bg-[#1a1333]/80 rounded-3xl shadow-2xl p-8 border border-[#A259F7]/30 backdrop-blur-md">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Image */}
            <div className="space-y-4">
              <div className="text-center">
                <h3 className="text-xl font-bold text-white">{leftDate}</h3>
                <p className="text-sm text-[#A259F7]">
                  {showSegmentation ? "With Segmentation" : "Original"}
                </p>
              </div>
              <div className="relative bg-[#221a36] rounded-2xl overflow-hidden border border-[#A259F7]/20" style={{ aspectRatio: "1/1" }}>
                <img
                  src={imagePaths.left}
                  alt={`Left MRI - Slice ${currentSlice + 1}`}
                  className="w-full h-full object-contain"
                  onLoad={() => setImagesLoaded(true)}
                  onError={(e) => {
                    console.error("Failed to load left image:", imagePaths.left);
                    (e.target as HTMLImageElement).src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzlDQTNBRiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=";
                  }}
                />
                {!imagesLoaded && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#A259F7]"></div>
                  </div>
                )}
              </div>
            </div>

            {/* Right Image */}
            <div className="space-y-4">
              <div className="text-center">
                <h3 className="text-xl font-bold text-white">{rightDate}</h3>
                <p className="text-sm text-[#A259F7]">
                  {showProgression
                    ? "Progression"
                    : showSegmentation
                      ? "With Segmentation"
                      : "Original"}
                </p>
              </div>
              <div className="relative bg-[#221a36] rounded-2xl overflow-hidden border border-[#A259F7]/20" style={{ aspectRatio: "1/1" }}>
                <img
                  src={imagePaths.right}
                  alt={`Right MRI - Slice ${currentSlice + 1}`}
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    console.error("Failed to load right image:", imagePaths.right);
                    (e.target as HTMLImageElement).src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzlDQTNBRiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=";
                  }}
                />
              </div>
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="flex justify-center items-center space-x-4 mt-8 pt-8 border-t border-[#A259F7]/20">
            <button
              onClick={() => setCurrentSlice(Math.max(0, currentSlice - 1))}
              disabled={currentSlice === 0}
              className="px-6 py-3 bg-gradient-to-r from-[#3B1E6D] to-[#A259F7] text-white rounded-xl hover:from-[#A259F7] hover:to-[#3B1E6D] transition-colors font-semibold shadow-lg border border-[#A259F7]/40 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ boxShadow: '0 0 8px #A259F7aa' }}
            >
              Previous
            </button>
            <span className="text-[#E0D7F7] font-semibold min-w-[120px] text-center">
              Slice {currentSlice + 1} of {totalSlices}
            </span>
            <button
              onClick={() => setCurrentSlice(Math.min(totalSlices - 1, currentSlice + 1))}
              disabled={currentSlice === totalSlices - 1}
              className="px-6 py-3 bg-gradient-to-r from-[#A259F7] to-[#3B1E6D] text-white rounded-xl hover:from-[#3B1E6D] hover:to-[#A259F7] transition-colors font-semibold shadow-lg border border-[#A259F7]/40 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ boxShadow: '0 0 8px #A259F7aa' }}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #A259F7;
          cursor: pointer;
          box-shadow: 0 0 2px 0 #555;
          transition: background .15s ease-in-out;
        }
        .slider::-webkit-slider-thumb:hover {
          background: #3B1E6D;
        }
        .slider::-moz-range-thumb {
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #A259F7;
          cursor: pointer;
          border: none;
          box-shadow: 0 0 2px 0 #555;
        }
      `}</style>
    </div>
  );
}
