import React, { useMemo } from 'react';

export function ProfessorReviewDashboard({ grades }) {
  const reviewItems = useMemo(
    () => grades.filter((item) => item.needs_human_review),
    [grades]
  );

  return (
    <div>
      <h1>AI Grading Review Dashboard</h1>
      <section>
        <h2>Quizzes Needing Human Review</h2>
        {reviewItems.length === 0 ? (
          <p>No edge cases detected by the AI.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Overall Score</th>
                <th>Reason</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reviewItems.map((grade) => (
                <tr key={grade.student_id} style={{ background: '#fff4e5' }}>
                  <td>{grade.student_id}</td>
                  <td>{grade.overall_score}</td>
                  <td>
                    {grade.question_evaluations.map((q) => (
                      <div key={q.question_number}>
                        Q{q.question_number}: {q.step_by_step_analysis.slice(0, 120)}...
                      </div>
                    ))}
                  </td>
                  <td>
                    <button type="button">Open Review</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
