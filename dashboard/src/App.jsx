import { useEffect, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [status, setStatus] = useState("Checking...");
  const [issues, setIssues] = useState([]);
  const [repositories, setRepositories] = useState([]);
  const [selectedRepository, setSelectedRepository] =
    useState("gitagent-ai");

  const [errorText, setErrorText] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => response.json())
      .then((data) => {
        setStatus(data.status);
      })
      .catch(() => {
        setStatus("Backend connection failed");
      });

    fetch(`${API_URL}/repositories`)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          setRepositories(data.repositories);

          if (data.repositories.length > 0) {
            setSelectedRepository(data.repositories[0]);
          }
        }
      })
      .catch(() => {
        setRepositories([]);
      });

    fetch(`${API_URL}/issues`)
      .then((response) => response.json())
      .then((data) => {
        setIssues(data);
      })
      .catch(() => {
        setIssues([]);
      });
  }, []);

  const analyzeError = async () => {
    if (!errorText.trim()) {
      return;
    }

    setLoading(true);
    setAnalysis(null);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          error: errorText,
          repository: selectedRepository,
        }),
      });

      const data = await response.json();

      setAnalysis(data);

      if (data.action === "new_issue_created") {
        fetch(`${API_URL}/issues`)
          .then((response) => response.json())
          .then((issueData) => {
            setIssues(issueData);
          });
      }
    } catch {
      setAnalysis({
        success: false,
        error: "Unable to connect to backend.",
      });
    }

    setLoading(false);
  };

  const relatedIssues =
    analysis?.similar_issues?.filter(
      (issue) => issue.is_related
    ) || [];

  const openIssues = issues.filter(
    (issue) => issue.state === "open"
  ).length;

  const closedIssues = issues.filter(
    (issue) => issue.state === "closed"
  ).length;

  return (
    <div className="app-layout">

      {/* Sidebar */}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">G</div>

          <div className="brand-text">
            <h1>GitAgent AI</h1>
            <p>Issue Intelligence</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div
  className="nav-link active"
  onClick={() =>
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    })
  }
>
  <span>◈</span>
  <span>Dashboard</span>
</div>

<div
  className="nav-link"
  onClick={() =>
    document
      .getElementById("issues-section")
      ?.scrollIntoView({
        behavior: "smooth",
      })
  }
>
  <span>◉</span>
  <span>Issues</span>
</div>

<div
  className="nav-link"
  onClick={() =>
    document
      .getElementById("ai-analysis")
      ?.scrollIntoView({
        behavior: "smooth",
      })
  }
>
  <span>✦</span>
  <span>AI Analysis</span>
</div>
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <span className="connection-dot"></span>

            <div>
              <strong>System Online</strong>
              <small>Services are ready</small>
            </div>
          </div>

          <p>AI-powered developer workflow</p>
        </div>
      </aside>

      {/* Main Content */}

      <main className="main-content">

        {/* Header */}

        <header className="page-header">
          <div>
            <span className="eyebrow">
              DEVELOPER CONTROL CENTER
            </span>

            <h2>Dashboard</h2>

            <p>
              Analyze application errors and intelligently
              manage GitHub issues.
            </p>
          </div>

          <div className="backend-status">
            <span
              className={
                status === "healthy"
                  ? "status-dot online"
                  : "status-dot offline"
              }
            ></span>

            <span>
              {status === "healthy"
                ? "Backend Connected"
                : status}
            </span>
          </div>
        </header>

        {/* Statistics */}

        <section className="stats-grid">

          <div className="stat-card">
            <div className="stat-icon blue">◎</div>

            <div>
              <span>Total Issues</span>
              <strong>{issues.length}</strong>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon green">✓</div>

            <div>
              <span>Open Issues</span>
              <strong>{openIssues}</strong>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon gray">✓</div>

            <div>
              <span>Closed Issues</span>
              <strong>{closedIssues}</strong>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon purple">◆</div>

            <div>
              <span>Repository</span>
              <strong className="repository-name">
                {selectedRepository}
              </strong>
            </div>
          </div>

        </section>

        {/* Analysis Area */}

        <section
  id="ai-analysis"
  className="analysis-grid"
>

          {/* Input */}

          <div className="panel analysis-panel">

            <div className="panel-header">
              <div>
                <span className="section-label">
                  AI WORKSPACE
                </span>

                <h3>Analyze Application Error</h3>

                <p>
                  Enter an application error and GitAgent AI
                  will analyze its severity and search for
                  related GitHub issues.
                </p>
              </div>

              <span className="ai-badge">
                ✦ AI Powered
              </span>
            </div>

            <div className="field">
              <label>Repository</label>

              <select
                value={selectedRepository}
                onChange={(e) =>
                  setSelectedRepository(e.target.value)
                }
              >
                {repositories.length > 0 ? (
                  repositories.map((repository) => (
                    <option
                      key={repository}
                      value={repository}
                    >
                      {repository}
                    </option>
                  ))
                ) : (
                  <option value="gitagent-ai">
                    gitagent-ai
                  </option>
                )}
              </select>
            </div>

            <div className="field">
              <label>Application Error</label>

              <textarea
                value={errorText}
                onChange={(e) =>
                  setErrorText(e.target.value)
                }
                placeholder="Example: CRITICAL payment gateway timeout while processing order"
                rows={7}
              />
            </div>

            <div className="action-row">
              <button
                className="analyze-button"
                onClick={analyzeError}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Analyzing...
                  </>
                ) : (
                  <>
                    Analyze Error
                    <span>→</span>
                  </>
                )}
              </button>

              <span className="action-note">
                GitHub-connected analysis
              </span>
            </div>

          </div>

          {/* Result */}

          <div className="panel result-panel">

            <div className="panel-header result-header">
              <div>
                <span className="section-label">
                  ANALYSIS
                </span>

                <h3>AI Result</h3>
              </div>

              <div className="result-icon">✦</div>
            </div>

            {!analysis && (
              <div className="empty-result">

                <div className="empty-icon">
                  ✦
                </div>

                <h4>Waiting for analysis</h4>

                <p>
                  Enter an application error and click
                  <strong> Analyze Error</strong> to see
                  the result.
                </p>

              </div>
            )}

            {analysis?.success && (
              <div className="result-content">

                <div className="severity-row">
                  <span>Detected Severity</span>

                  <span
                    className={`severity-badge ${analysis.severity.toLowerCase()}`}
                  >
                    {analysis.severity}
                  </span>
                </div>

                <div className="divider"></div>

                <div className="repository-row">
                  <span>Repository</span>
                  <strong>{selectedRepository}</strong>
                </div>

                {analysis.action ===
                  "existing_issue_found" && (
                  <div className="result-section">

                    <h4>Related GitHub Issues</h4>

                    {relatedIssues.length > 0 ? (
                      relatedIssues.map((issue) => (
                        <div
                          className="match-card"
                          key={issue.issue_number}
                        >
                          <div className="match-top">
                            <strong>
                              #{issue.issue_number}
                            </strong>

                            <span>
                              {(issue.score * 100).toFixed(1)}%
                            </span>
                          </div>

                          <p>{issue.title}</p>

                          <small>
                            Semantic similarity match
                          </small>
                        </div>
                      ))
                    ) : (
                      <p className="muted">
                        No related issue passed the
                        similarity threshold.
                      </p>
                    )}

                  </div>
                )}

                {analysis.action ===
                  "new_issue_created" && (
                  <div className="created-card">

                    <div className="created-icon">
                      ✓
                    </div>

                    <div>
                      <h4>New GitHub Issue Created</h4>

                      <p>
                        No sufficiently similar existing
                        issue was found.
                      </p>

                      {analysis.created_issue?.success && (
                        <a
                          href={
                            analysis.created_issue.url
                          }
                          target="_blank"
                          rel="noreferrer"
                        >
                          View Issue #
                          {
                            analysis.created_issue
                              .issue_number
                          }{" "}
                          on GitHub →
                        </a>
                      )}
                    </div>

                  </div>
                )}

              </div>
            )}

            {analysis && !analysis.success && (
              <div className="error-card">
                <strong>Analysis Failed</strong>
                <p>{analysis.error}</p>
              </div>
            )}

          </div>

        </section>

        {/* GitHub Issues */}

        <section
  id="issues-section"
  className="issues-section"
>

          <div className="issues-header">

            <div>
              <span className="section-label">
                GITHUB INTEGRATION
              </span>

              <h3>Repository Issues</h3>

              <p>
                Live issues from{" "}
                <strong>{selectedRepository}</strong>
              </p>
            </div>

            <span className="issue-count">
              {issues.length} issues
            </span>

          </div>

          <div className="issues-grid">

            {issues.map((issue) => (
              <article
                className="github-card"
                key={issue.id}
              >

                <div className="github-card-top">

                  <span className="issue-number">
                    #{issue.number}
                  </span>

                  <span
                    className={`state-badge ${issue.state}`}
                  >
                    {issue.state}
                  </span>

                </div>

                <h4>{issue.title}</h4>

                <div className="issue-meta">
                  💬 {issue.comments} comments
                </div>

                <a
                  href={issue.html_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open on GitHub →
                </a>

              </article>
            ))}

          </div>

        </section>

        {/* Footer */}

        <footer className="footer">
          <span>GitAgent AI</span>
          <span>
            AI-powered GitHub Issue Management
          </span>
        </footer>

      </main>
    </div>
  );
}

export default App;