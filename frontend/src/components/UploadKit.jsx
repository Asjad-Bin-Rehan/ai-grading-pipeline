import React, { useState } from 'react';

export function UploadKit({ onKitUploaded, loading }) {
  const [masterKeyFile, setMasterKeyFile] = useState(null);
  const [rubricFile, setRubricFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleMasterKeyChange = (e) => {
    setMasterKeyFile(e.target.files[0]);
    setError(null);
  };

  const handleRubricChange = (e) => {
    setRubricFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async () => {
    if (!masterKeyFile || !rubricFile) {
      setError('Please select both master key and rubric files');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('master_key', masterKeyFile);
      formData.append('rubric', rubricFile);

      const response = await fetch('http://localhost:8000/upload-kit', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload kit');
      }

      const data = await response.json();
      setSuccess('Kit uploaded successfully!');
      setMasterKeyFile(null);
      setRubricFile(null);
      
      // Reset file inputs
      document.getElementById('master-key-input').value = '';
      document.getElementById('rubric-input').value = '';

      onKitUploaded(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-section">
      <h2>Step 1: Upload Grading Kit</h2>
      <p className="section-description">Upload the master answer key and rubric for grading</p>

      <div className="form-group">
        <label htmlFor="master-key-input">Master Answer Key (DOCX or PDF)</label>
        <input
          id="master-key-input"
          type="file"
          accept=".docx,.pdf"
          onChange={handleMasterKeyChange}
          disabled={uploading}
        />
        {masterKeyFile && (
          <span className="file-selected">✓ {masterKeyFile.name}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="rubric-input">Grading Rubric (DOCX or PDF)</label>
        <input
          id="rubric-input"
          type="file"
          accept=".docx,.pdf"
          onChange={handleRubricChange}
          disabled={uploading}
        />
        {rubricFile && (
          <span className="file-selected">✓ {rubricFile.name}</span>
        )}
      </div>

      <button
        onClick={handleUpload}
        disabled={uploading || !masterKeyFile || !rubricFile || loading}
        className="btn btn-primary"
      >
        {uploading ? 'Uploading...' : 'Upload Kit'}
      </button>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
    </div>
  );
}
