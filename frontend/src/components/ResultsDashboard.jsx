import React, { useEffect, useState } from 'react';

export function ResultsDashboard({ refreshTrigger }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, flagged, passed
  const [expandedStudent, setExpandedStudent] = useState(null);

  useEffect(() => {
    fetchResults();
  }, [refreshTrigger]);

  const fetchResults = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/results');
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredResults = results.filter((result) => {
    if (filter === 'flagged') return result.needs_human_review;
    if (filter === 'passed') return !result.needs_human_review;
    return true;
  });

  const stats = {
    total: results.length,
    flagged: results.filter((r) => r.needs_human_review).length,
    averageScore: results.length > 0
      ? (results.reduce((sum, r) => sum + r.overall_score, 0) / results.length).toFixed(1)
      : 0,
  };

  return (
    <div className="results-section">
      <h2>Step 3: Grading Results</h2>

      {error && <div className="error-message">Error: {error}</div>}

      {loading ? (
        <p className="loading">Loading results...</p>
      ) : (
        <>
          {/* Statistics */}
          <div className="stats-grid">
            <div className="stat-card">
              <h3>{stats.total}</h3>
              <p>Total Submissions</p>
            </div>
            <div className="stat-card stat-warning">
              <h3>{stats.flagged}</h3>
              <p>Flagged for Review</p>
            </div>
            <div className="stat-card">
              <h3>{stats.averageScore}</h3>
              <p>Average Score</p>
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="filter-tabs">
            <button
              className={`tab ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              All ({results.length})
            </button>
            <button
              className={`tab ${filter === 'flagged' ? 'active' : ''}`}
              onClick={() => setFilter('flagged')}
            >
              Flagged ({stats.flagged})
            </button>
            <button
              className={`tab ${filter === 'passed' ? 'active' : ''}`}
              onClick={() => setFilter('passed')}
            >
              Passed ({results.length - stats.flagged})
            </button>
          </div>

          {/* Results Table */}
          {filteredResults.length === 0 ? (
            <p className="no-results">
              {filter === 'flagged'
                ? 'No submissions flagged for human review'
                : 'No results to display'}
            </p>
          ) : (
            <div className="results-table-container">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Overall Score</th>
                    <th>Status</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredResults.map((result) => (
                    <React.Fragment key={result.student_id}>
                      <tr className={result.needs_human_review ? 'flagged' : ''}>
                        <td className="student-id">{result.student_id}</td>
                        <td className="score">
                          <strong>{result.overall_score.toFixed(1)}</strong>
                        </td>
                        <td className="status">
                          {result.needs_human_review ? (
                            <span className="badge badge-warning">⚠️ Needs Review</span>
                          ) : (
                            <span className="badge badge-success">✓ Passed</span>
                          )}
                        </td>
                        <td className="actions">
                          <button
                            className="btn-expand"
                            onClick={() =>
                              setExpandedStudent(
                                expandedStudent === result.student_id
                                  ? null
                                  : result.student_id
                              )
                            }
                          >
                            {expandedStudent === result.student_id ? '▼' : '▶'}
                          </button>
                        </td>
                      </tr>
                      {expandedStudent === result.student_id && (
                        <tr className="details-row">
                          <td colSpan="4">
                            <div className="details-content">
                              <h5>Question Evaluations</h5>
                              {result.question_evaluations.map((q, idx) => (
                                <div key={idx} className="question-detail">
                                  <div className="question-header">
                                    <strong>Question {q.question_number}</strong>
                                    <span className="points">
                                      Points: {q.points_awarded}
                                    </span>
                                  </div>
                                  <p className="analysis">
                                    {q.step_by_step_analysis}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <button onClick={fetchResults} className="btn btn-secondary">
            🔄 Refresh Results
          </button>
        </>
      )}
    </div>
  );
}
