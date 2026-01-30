import React, { useState } from 'react';
import axios from 'axios';
import './Upload.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Upload() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setResult(null);

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API_URL}/embed`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
      setFiles([]);
    } catch (error) {
      setResult({ status: 'error', message: error.message });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h1>📄 Document Upload</h1>
        <p className="subtitle">Upload insurance policy documents for compliance analysis</p>

        <div className="upload-area">
          <input
            type="file"
            multiple
            accept=".pdf,.docx"
            onChange={handleFileChange}
            id="file-input"
            className="file-input"
          />
          <label htmlFor="file-input" className="file-label">
            <div className="upload-icon">📁</div>
            <div>Choose PDF or DOCX files</div>
            <div className="file-hint">or drag and drop</div>
          </label>
        </div>

        {files.length > 0 && (
          <div className="file-list">
            <h3>Selected Files:</h3>
            {files.map((file, idx) => (
              <div key={idx} className="file-item">
                📄 {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </div>
            ))}
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={uploading || files.length === 0}
          className="upload-button"
        >
          {uploading ? '⏳ Processing...' : '🚀 Upload & Embed'}
        </button>

        {result && (
          <div className={`result ${result.status}`}>
            <h3>{result.status === 'success' ? '✅ Success' : '❌ Error'}</h3>
            <p>{result.message}</p>
            {result.files_processed && (
              <div className="processed-files">
                {result.files_processed.map((name, idx) => (
                  <div key={idx}>• {name}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
