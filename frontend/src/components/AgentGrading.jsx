import React, { useState } from 'react';
import { apiUrl } from '../api';

const TERMINAL_STATUSES = new Set(['completed', 'partial', 'failed']);
const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 300000;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchAgentReport(report) {
  const response = await fetch(apiUrl('/agent/report'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      run_id: report.run_id,
      kit: report.kit,
      tasks: report.tasks,
    }),
  });
  return response;
}

export function AgentGrading({ onRunComplete }) {
  const [masterKeyFile, setMasterKeyFile] = useState(null);
  const [rubricFile, setRubricFile] = useState(null);
  const [quizFiles, setQuizFiles] = useState([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [progressText, setProgressText] = useState('');

  const handleRunAgent = async () => {
    if (!masterKeyFile || !rubricFile) {
      setError('Please select both master key and rubric files');
      return;
    }
    if (quizFiles.length === 0) {
      setError('Please select at least one student quiz');
      return;
    }

    setRunning(true);
    setError(null);
    setReport(null);
    setProgressText('Uploading files and queuing grading jobs...');

    try {
      const formData = new FormData();
      formData.append('master_key', masterKeyFile);
      formData.append('rubric', rubricFile);
      quizFiles.forEach((file) => formData.append('submissions', file));

      const response = await fetch(apiUrl('/agent/run'), {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || 'Agent run failed');
      }

      let currentReport = await response.json();
      setReport(currentReport);

      const deadline = Date.now() + POLL_TIMEOUT_MS;
      while (!TERMINAL_STATUSES.has(currentReport.status) && Date.now() < deadline) {
        setProgressText(
          `Grading ${currentReport.completed_count}/${currentReport.submitted_count} complete ` +
            `(${currentReport.failed_count} failed, ${currentReport.pending_count} pending)...`
        );
        await sleep(POLL_INTERVAL_MS);

        const statusResponse = await fetchAgentReport(currentReport);
        if (!statusResponse.ok) {
          throw new Error('Failed to fetch grading progress');
        }
        currentReport = await statusResponse.json();
        setReport(currentReport);
      }

      if (!TERMINAL_STATUSES.has(currentReport.status)) {
        throw new Error('Grading timed out. Check results dashboard or try again.');
      }

      onRunComplete?.(currentReport);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
      setProgressText('');
    }
  };

  return (
    <div className="upload-section agent-section">
      <h2>Auto Grade (Agent)</h2>
      <p className="section-description">
        Upload kit and student quizzes in one step. The agent handles batch grading and returns a summary.
      </p>

      <div className="form-group">
        <label htmlFor="agent-master-key">Master Answer Key</label>
        <input
          id="agent-master-key"
          type="file"
          accept=".docx,.pdf"
          onChange={(e) => setMasterKeyFile(e.target.files[0] || null)}
          disabled={running}
        />
      </div>

      <div className="form-group">
        <label htmlFor="agent-rubric">Grading Rubric</label>
        <input
          id="agent-rubric"
          type="file"
          accept=".docx,.pdf"
          onChange={(e) => setRubricFile(e.target.files[0] || null)}
          disabled={running}
        />
      </div>

      <div className="form-group">
        <label htmlFor="agent-quizzes">Student Quiz Files</label>
        <input
          id="agent-quizzes"
          type="file"
          accept=".docx,.pdf"
          multiple
          onChange={(e) => setQuizFiles(Array.from(e.target.files || []))}
          disabled={running}
        />
        {quizFiles.length > 0 && (
          <p className="helper-text">{quizFiles.length} file(s) selected</p>
        )}
      </div>

      {running && progressText && (
        <div className="progress-container">
          <p className="progress-text">{progressText}</p>
        </div>
      )}

      <button
        type="button"
        onClick={handleRunAgent}
        disabled={running}
        className="btn btn-primary"
      >
        {running ? 'Agent running...' : 'Run Grading Agent'}
      </button>

      {error && <div className="error-message">{error}</div>}

      {report && (
        <div className="agent-report">
          <h3>Agent Run Summary</h3>
          <p>{report.summary}</p>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>{report.submitted_count}</h3>
              <p>Submitted</p>
            </div>
            <div className="stat-card">
              <h3>{report.completed_count}</h3>
              <p>Completed</p>
            </div>
            <div className="stat-card stat-warning">
              <h3>{report.flagged_count}</h3>
              <p>Flagged</p>
            </div>
            <div className="stat-card">
              <h3>{report.average_score?.toFixed(1) ?? '—'}</h3>
              <p>Average Score</p>
            </div>
          </div>
          <p className="helper-text">Run status: {report.status}</p>
          {report.tasks?.some((task) => task.status === 'FAILURE') && (
            <div className="error-message">
              <strong>Failed tasks:</strong>
              <ul>
                {report.tasks
                  .filter((task) => task.status === 'FAILURE')
                  .map((task) => (
                    <li key={task.task_id}>
                      {task.student_id}: {task.error || 'Unknown error'}
                    </li>
                  ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
