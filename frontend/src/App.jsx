import { useState } from 'react';
import { UploadKit } from './components/UploadKit';
import { UploadStudentQuizzes } from './components/UploadStudentQuizzes';
import { AgentGrading } from './components/AgentGrading';
import { ChatAssistant } from './components/ChatAssistant';
import { ResultsDashboard } from './components/ResultsDashboard';

function App() {
  const [kitData, setKitData] = useState(null);
  const [refreshResults, setRefreshResults] = useState(0);
  const [appLoading, setAppLoading] = useState(false);

  const handleKitUploaded = (data) => {
    setKitData(data);
  };

  const handleGradingStarted = () => {
    // Refresh results after a delay to allow backend processing
    setTimeout(() => {
      setRefreshResults((prev) => prev + 1);
    }, 1000);
  };

  const handleAgentComplete = () => {
    setRefreshResults((prev) => prev + 1);
  };

  return (
    <div className="app-shell">
      <header>
        <div className="header-content">
          <h1>📚 AI Grading Pipeline</h1>
          <p>
            Upload your grading kit and student quizzes to automatically grade with AI
          </p>
        </div>
      </header>

      <main className="main-content">
        <AgentGrading onRunComplete={handleAgentComplete} />

        <ChatAssistant />

        {/* Step 1: Upload Kit */}
        <UploadKit onKitUploaded={handleKitUploaded} loading={appLoading} />

        {/* Step 2: Upload Student Quizzes */}
        <UploadStudentQuizzes
          kitData={kitData}
          onGradingStarted={handleGradingStarted}
          loading={appLoading}
        />

        {/* Step 3: Results Dashboard */}
        <ResultsDashboard refreshTrigger={refreshResults} />
      </main>

      <footer>
        <p>© 2026 AI Grading Pipeline | Powered by FastAPI + Celery</p>
      </footer>
    </div>
  );
}

export default App;
