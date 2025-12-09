// frontend/src/App.jsx - Enhanced with Real-World Features
import React, { useState, useCallback } from 'react';
import { summarizeText } from './services/api';

function App() {
  const [text, setText] = useState('');
  const [mode, setMode] = useState('extractive');
  const [topK, setTopK] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);

  // Handle file upload (PDF, TXT, DOCX, etc.)
  const handleFileUpload = useCallback(async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadedFile(file.name);
    setError(null);

    // Handle different file types
    if (file.type === 'text/plain') {
      const text = await file.text();
      setText(text);
    } else if (file.type === 'application/pdf') {
      setError('PDF upload: Please use backend API endpoint for PDF processing');
      // In production, send to backend endpoint that handles PDFs
    } else if (file.type.includes('word')) {
      setError('DOCX upload: Please use backend API endpoint for Word document processing');
      // In production, send to backend endpoint that handles DOCX
    } else {
      try {
        const text = await file.text();
        setText(text);
      } catch (err) {
        setError('Unable to read file. Please try a text file.');
      }
    }
  }, []);

  // Handle drag and drop
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const fakeEvent = { target: { files: [file] } };
      handleFileUpload(fakeEvent);
    }
  }, [handleFileUpload]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Please enter some text to summarize');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await summarizeText({
        text: text,
        mode: mode,
        top_k: topK,
        include_provenance: true
      });
      
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to summarize text');
    } finally {
      setLoading(false);
    }
  };

  const loadExample = () => {
    setText(`Subject: Login issues after password reset

Customer reported inability to access account after completing password reset process. User followed the reset link from email but receives "Invalid session" error on login page.

Steps to reproduce:
1. Click forgot password
2. Receive reset email
3. Click reset link
4. Set new password
5. Attempt to login

Expected result: Successful login with new credentials
Actual result: Invalid session error displayed

Resolution: Cleared browser cache and cookies. Session tokens were stale. User successfully logged in after cache clear. Recommended enabling "Remember me" option to prevent future issues.`);
    setUploadedFile(null);
  };

  const clearText = () => {
    setText('');
    setResult(null);
    setError(null);
    setUploadedFile(null);
  };

  const copyToClipboard = () => {
    if (result?.summary) {
      navigator.clipboard.writeText(result.summary);
      alert('Summary copied to clipboard!');
    }
  };

  const downloadSummary = () => {
    if (result?.summary) {
      const blob = new Blob([result.summary], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'summary.txt';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">
                RAG Customer Support Summarizer
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                Intelligent text summarization with multiple pipeline modes
              </p>
            </div>
            <div className="text-right text-xs text-slate-500">
              <div>Multiple Input Methods</div>
              <div className="font-medium text-blue-600">Paste • Upload • Integrate</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-slate-900">Input Text</h2>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Ready
              </span>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Upload Section */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Input Method
                </label>
                
                {/* File Upload / Drag & Drop */}
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  className="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center hover:border-blue-500 transition-colors"
                >
                  <input
                    type="file"
                    id="file-upload"
                    accept=".txt,.csv,.pdf,.doc,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer"
                  >
                    <div className="text-slate-600">
                      <svg className="mx-auto h-8 w-8 mb-2 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <span className="text-sm">
                        <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
                      </span>
                      <p className="text-xs text-slate-500 mt-1">
                        TXT, CSV, PDF, DOC, DOCX (max 10MB)
                      </p>
                    </div>
                  </label>
                  {uploadedFile && (
                    <div className="mt-2 text-sm text-green-600">
                      Uploaded: {uploadedFile}
                    </div>
                  )}
                </div>

                <div className="text-center text-xs text-slate-500 my-2">OR</div>
              </div>

              {/* Text Input */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label htmlFor="text" className="block text-sm font-medium text-slate-700">
                    Paste Support Ticket
                  </label>
                  {text && (
                    <button
                      type="button"
                      onClick={clearText}
                      className="text-xs text-red-600 hover:text-red-700"
                    >
                      Clear
                    </button>
                  )}
                </div>
                <textarea
                  id="text"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="w-full h-48 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
                  placeholder="Paste customer support ticket, chat log, or email here..."
                />
                <div className="flex justify-between items-center mt-1">
                  <span className="text-xs text-slate-500">
                    {text.length} characters
                  </span>
                  {text.length > 5000 && (
                    <span className="text-xs text-amber-600">
                      Large text may take longer to process
                    </span>
                  )}
                </div>
              </div>

              {/* Pipeline Mode */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Pipeline Mode
                </label>
                <div className="flex gap-2 p-1 bg-slate-100 rounded-lg">
                  {['extractive', 'semantic', 'abstractive'].map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setMode(m)}
                      className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                        mode === m
                          ? 'bg-white text-blue-600 shadow'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      {m.charAt(0).toUpperCase() + m.slice(1)}
                    </button>
                  ))}
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {mode === 'extractive' && 'Fast TextRank-only (~200ms) - Best for speed'}
                  {mode === 'semantic' && 'TextRank + DistilBERT (~350ms) - Balanced quality'}
                  {mode === 'abstractive' && 'Full LLM pipeline (~1200ms) - Best quality'}
                </p>
              </div>

              {/* Top K */}
              <div>
                <label htmlFor="topk" className="block text-sm font-medium text-slate-700 mb-2">
                  Sentences to Extract: {topK}
                </label>
                <input
                  type="range"
                  id="topk"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  min="1"
                  max="10"
                  className="w-full"
                />
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Processing...' : 'Summarize'}
                </button>
                <button
                  type="button"
                  onClick={loadExample}
                  className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-300 transition-colors"
                >
                  Load Example
                </button>
              </div>

              {/* Integration Info */}
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-xs text-blue-900 font-medium mb-1">
                  For Production Use
                </p>
                <p className="text-xs text-blue-700">
                  Integrate via API, Email, Slack, Zendesk, or direct database connection
                </p>
              </div>
            </form>
          </div>

          {/* Output Panel */}
          <div className="bg-white rounded-lg shadow border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-slate-900">Summary Output</h2>
              <div className="flex items-center gap-2">
                {result && (
                  <>
                    <button
                      onClick={copyToClipboard}
                      className="text-xs px-3 py-1 bg-slate-100 text-slate-700 rounded hover:bg-slate-200 transition-colors"
                      title="Copy to clipboard"
                    >
                      Copy
                    </button>
                    <button
                      onClick={downloadSummary}
                      className="text-xs px-3 py-1 bg-slate-100 text-slate-700 rounded hover:bg-slate-200 transition-colors"
                      title="Download as text file"
                    >
                      Download
                    </button>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Complete
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Error State */}
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Empty State */}
            {!result && !loading && !error && (
              <div className="text-center py-12 text-slate-500">
                <svg className="mx-auto h-16 w-16 text-slate-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="font-medium">Upload, paste, or integrate</p>
                <p className="text-sm mt-1">Summary will appear here after processing</p>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-sm text-slate-600">
                  Processing with {mode} mode...
                </p>
              </div>
            )}

            {/* Result */}
            {result && (
              <div className="space-y-6">
                {/* Summary */}
                <div className="bg-slate-50 border-l-4 border-blue-600 p-4 rounded">
                  <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2">
                    Generated Summary
                  </h3>
                  <p className="text-slate-900 leading-relaxed">
                    {result.summary}
                  </p>
                </div>

                {/* Extracted Sentences */}
                <div>
                  <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-3">
                    Extracted Sentences
                  </h3>
                  <div className="space-y-2">
                    {result.sentences_extracted.map((sentence, idx) => (
                      <div key={idx} className="bg-white border border-slate-200 rounded p-3 text-sm text-slate-700">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-medium mr-2">
                          {idx + 1}
                        </span>
                        {sentence}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Metrics Panel */}
        {result && (
          <div className="mt-6 bg-white rounded-lg shadow border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-6">Performance Metrics</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div className="text-xs font-medium text-slate-600 uppercase tracking-wide">
                  Pipeline Mode
                </div>
                <div className="mt-2 text-2xl font-semibold text-slate-900">
                  {result.mode}
                </div>
              </div>
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div className="text-xs font-medium text-slate-600 uppercase tracking-wide">
                  Total Duration
                </div>
                <div className="mt-2 text-2xl font-semibold text-slate-900">
                  {Math.round(result.total_duration_ms)}ms
                </div>
              </div>
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div className="text-xs font-medium text-slate-600 uppercase tracking-wide">
                  Sentences
                </div>
                <div className="mt-2 text-2xl font-semibold text-slate-900">
                  {result.sentences_extracted.length}
                </div>
              </div>
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div className="text-xs font-medium text-slate-600 uppercase tracking-wide">
                  Cache Hit
                </div>
                <div className="mt-2 text-2xl font-semibold text-slate-900">
                  {result.cache_hit ? 'Yes' : 'No'}
                </div>
              </div>
            </div>

            {result.pipeline_stages && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-4">Pipeline Stages</h3>
                <div className="space-y-2">
                  {result.pipeline_stages.map((stage, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="w-40 text-sm font-medium text-slate-600">
                        {stage.name}
                      </div>
                      <div className="flex-1 bg-slate-100 rounded-full h-6 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-blue-600 h-full flex items-center justify-end px-2 transition-all duration-500"
                          style={{ width: `${Math.min(100, (stage.duration_ms / 800) * 100)}%` }}
                        >
                          <span className="text-xs font-semibold text-white">
                            {Math.round(stage.duration_ms)}ms
                          </span>
                        </div>
                      </div>
                      <span className="text-green-500">✓</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;