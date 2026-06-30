import React, { useState } from 'react';

export function UploadStudentQuizzes({ kitData, onGradingStarted, loading }) {
  const [quizFiles, setQuizFiles] = useState([]);
  const [grading, setGrading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [gradingProgress, setGradingProgress] = useState(0);

  const handleQuizFilesChange = (e) => {
    setQuizFiles(Array.from(e.target.files));
    setError(null);
  };

  const handleRemoveFile = (index) => {
    setQuizFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleGradeAll = async () => {
    if (quizFiles.length === 0) {
      setError('Please select at least one student quiz');
      return;
    }

    if (!kitData) {
      setError('Please upload the grading kit first');
      return;
    }

    setGrading(true);
    setError(null);
    setSuccess(null);
    setGradingProgress(0);

    try {
      for (let i = 0; i < quizFiles.length; i++) {
        const file = quizFiles[i];
        
        // Generate student ID from filename or use index
        const studentId = file.name.replace(/\.[^/.]+$/, '') || `student_${i + 1}`;

        const formData = new FormData();
        formData.append('submission', file);
        formData.append('student_id', studentId);
        formData.append('master_key_path', kitData.master_key_path);
        formData.append('rubric_path', kitData.rubric_path);

        const response = await fetch('http://localhost:8000/grade/submit', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Failed to grade ${file.name}`);
        }

        setGradingProgress(((i + 1) / quizFiles.length) * 100);
      }

      setSuccess(`✓ All ${quizFiles.length} quizzes submitted for grading!`);
      setQuizFiles([]);
      document.getElementById('quiz-files-input').value = '';
      onGradingStarted();
    } catch (err) {
      setError(err.message);
    } finally {
      setGrading(false);
    }
  };

  return (
    <div className="upload-section">
      <h2>Step 2: Upload Student Quizzes</h2>
      <p className="section-description">Select student quiz files to grade (DOCX or PDF)</p>

      {!kitData && (
        <div className="warning-message">
          ⚠️ Please upload the grading kit first in Step 1
        </div>
      )}

      <div className="form-group">
        <label htmlFor="quiz-files-input">Student Quiz Files</label>
        <input
          id="quiz-files-input"
          type="file"
          accept=".docx,.pdf"
          multiple
          onChange={handleQuizFilesChange}
          disabled={grading || !kitData}
        />
        <p className="helper-text">You can select multiple files at once</p>
      </div>

      {quizFiles.length > 0 && (
        <div className="file-list">
          <h4>Selected Files ({quizFiles.length})</h4>
          <ul>
            {quizFiles.map((file, index) => (
              <li key={index}>
                <span>{file.name}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveFile(index)}
                  disabled={grading}
                  className="btn-remove"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {grading && (
        <div className="progress-container">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${gradingProgress}%` }}
            ></div>
          </div>
          <p className="progress-text">
            Grading: {Math.round(gradingProgress)}% ({Math.round((gradingProgress / 100) * quizFiles.length)}/{quizFiles.length})
          </p>
        </div>
      )}

      <button
        onClick={handleGradeAll}
        disabled={grading || quizFiles.length === 0 || !kitData || loading}
        className="btn btn-primary"
      >
        {grading ? 'Grading...' : `Grade ${quizFiles.length} Quiz${quizFiles.length !== 1 ? 'zes' : ''}`}
      </button>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
    </div>
  );
}
