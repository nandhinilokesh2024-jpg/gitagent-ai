import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("Checking...");
  const [issues, setIssues] = useState([]);

  const [repositories, setRepositories] = useState([]);
  const [selectedRepository, setSelectedRepository] =
    useState("gitagent-ai");

  const [errorText, setErrorText] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  // --------------------------------
  // Load backend status, repositories
  // and GitHub issues
  // --------------------------------

  useEffect(() => {
    // Backend health
    fetch("http://127.0.0.1:8000/health")
      .then((response) => response.json())
      .then((data) => {
        setStatus(data.status);
      })
      .catch(() => {
        setStatus("Backend connection failed");
      });

    // Load repositories
    fetch("http://127.0.0.1:8000/repositories")
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

    // Load GitHub issues
    fetch("http://127.0.0.1:8000/issues")
      .then((response) => response.json())
      .then((data) => {
        setIssues(data);
      })
      .catch(() => {
        setIssues([]);
      });
  }, []);

  // --------------------------------
  // Analyze Application Error
  // --------------------------------

  const analyzeError = async () => {
    if (!errorText.trim()) {
      return;
    }

    setLoading(true);
    setAnalysis(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/analyze",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            error: errorText,
            repository: selectedRepository,
          }),
        }
      );

      const data = await response.json();

      setAnalysis(data);

      // Refresh GitHub issues after a new issue is created
      if (data.action === "new_issue_created") {
        fetch("http://127.0.0.1:8000/issues")
          .then((response) => response.json())
          .then((issueData) => {
            setIssues(issueData);
          });
      }
    } catch (error) {
      setAnalysis({
        success: false,
        error: "Unable to connect to backend.",
      });
    }

    setLoading(false);
  };

  // --------------------------------
  // Related Issues
  // --------------------------------

  const relatedIssues =
    analysis?.similar_issues?.filter(
      (issue) => issue.is_related
    ) || [];

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#f4f7fb",
        padding: "30px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      {/* Header */}

      <div
        style={{
          backgroundColor: "#111827",
          color: "white",
          padding: "25px",
          borderRadius: "12px",
          marginBottom: "25px",
        }}
      >
        <h1 style={{ margin: 0 }}>GitAgent AI</h1>

        <p style={{ marginBottom: 0 }}>
          AI-powered GitHub Issue Management
        </p>
      </div>

      {/* Statistics */}

      <div
        style={{
          display: "flex",
          gap: "20px",
          flexWrap: "wrap",
          marginBottom: "30px",
        }}
      >
        {/* Backend Status */}

        <div
          style={{
            backgroundColor: "white",
            padding: "20px",
            borderRadius: "10px",
            minWidth: "180px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <h3>Backend Status</h3>

          <p
            style={{
              color: status === "healthy" ? "green" : "red",
              fontWeight: "bold",
            }}
          >
            ● {status}
          </p>
        </div>

        {/* Total Issues */}

        <div
          style={{
            backgroundColor: "white",
            padding: "20px",
            borderRadius: "10px",
            minWidth: "180px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <h3>Total Issues</h3>

          <p
            style={{
              fontSize: "28px",
              fontWeight: "bold",
              margin: 0,
            }}
          >
            {issues.length}
          </p>
        </div>

        {/* Repository */}

        <div
          style={{
            backgroundColor: "white",
            padding: "20px",
            borderRadius: "10px",
            minWidth: "220px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <h3>Repository</h3>

          <select
            value={selectedRepository}
            onChange={(e) =>
              setSelectedRepository(e.target.value)
            }
            style={{
              padding: "10px",
              borderRadius: "8px",
              border: "1px solid #d1d5db",
              fontSize: "15px",
              width: "100%",
            }}
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
      </div>

      {/* Analyze Error */}

      <div
        style={{
          backgroundColor: "white",
          padding: "25px",
          borderRadius: "12px",
          marginBottom: "30px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
        }}
      >
        <h2>Analyze Application Error</h2>

        <p style={{ color: "#6b7280" }}>
          Enter an application error and let GitAgent AI
          analyze it using severity detection and RAG.
        </p>

        <textarea
          value={errorText}
          onChange={(e) => setErrorText(e.target.value)}
          placeholder="Example: Email service failed to send notification"
          rows="5"
          style={{
            width: "100%",
            padding: "12px",
            borderRadius: "8px",
            border: "1px solid #d1d5db",
            fontSize: "16px",
            boxSizing: "border-box",
            resize: "vertical",
          }}
        />

        <button
          onClick={analyzeError}
          disabled={loading}
          style={{
            marginTop: "15px",
            padding: "12px 22px",
            backgroundColor: loading
              ? "#9ca3af"
              : "#2563eb",
            color: "white",
            border: "none",
            borderRadius: "8px",
            fontSize: "16px",
            fontWeight: "bold",
            cursor: loading
              ? "not-allowed"
              : "pointer",
          }}
        >
          {loading ? "Analyzing..." : "Analyze Error"}
        </button>
      </div>

      {/* Analysis Result */}

      {analysis && analysis.success && (
        <div
          style={{
            backgroundColor: "white",
            padding: "25px",
            borderRadius: "12px",
            marginBottom: "30px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <h2>Analysis Result</h2>

          {/* Selected Repository */}

          <p style={{ color: "#6b7280" }}>
            Repository:{" "}
            <strong>{selectedRepository}</strong>
          </p>

          {/* Severity */}

          <div
            style={{
              display: "inline-block",
              padding: "8px 14px",
              borderRadius: "20px",
              backgroundColor:
                analysis.severity === "CRITICAL"
                  ? "#fee2e2"
                  : analysis.severity === "HIGH"
                  ? "#ffedd5"
                  : analysis.severity === "MEDIUM"
                  ? "#fef3c7"
                  : "#dcfce7",
              fontWeight: "bold",
              marginBottom: "20px",
            }}
          >
            Severity: {analysis.severity}
          </div>

          {/* Existing Issue Found */}

          {analysis.action === "existing_issue_found" && (
            <>
              <h3>Similar GitHub Issues</h3>

              {relatedIssues.length > 0 ? (
                relatedIssues.map((issue) => (
                  <div
                    key={issue.issue_number}
                    style={{
                      border: "1px solid #e5e7eb",
                      borderRadius: "10px",
                      padding: "18px",
                      marginTop: "12px",
                    }}
                  >
                    <h3>
                      #{issue.issue_number} — {issue.title}
                    </h3>

                    <p>
                      Similarity:{" "}
                      <strong>
                        {(issue.score * 100).toFixed(1)}%
                      </strong>
                    </p>

                    <p>
                      This issue appears related to the
                      entered application error.
                    </p>
                  </div>
                ))
              ) : (
                <p>
                  An existing issue was found, but no
                  related issue passed the similarity
                  threshold.
                </p>
              )}
            </>
          )}

          {/* New Issue Created */}

          {analysis.action === "new_issue_created" && (
            <div
              style={{
                marginTop: "10px",
                padding: "20px",
                borderRadius: "10px",
                backgroundColor: "#eff6ff",
                border: "1px solid #bfdbfe",
              }}
            >
              <h3>New GitHub Issue Created</h3>

              <p>
                No sufficiently similar existing issue was
                found.
              </p>

              {analysis.created_issue?.success && (
                <>
                  <p>
                    Issue{" "}
                    <strong>
                      #{analysis.created_issue.issue_number}
                    </strong>{" "}
                    was created automatically.
                  </p>

                  <a
                    href={analysis.created_issue.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      color: "#2563eb",
                      fontWeight: "bold",
                      textDecoration: "none",
                    }}
                  >
                    View New GitHub Issue →
                  </a>
                </>
              )}
            </div>
          )}

          {/* Fallback */}

          {analysis.action !== "existing_issue_found" &&
            analysis.action !== "new_issue_created" &&
            relatedIssues.length === 0 && (
              <p>
                No related GitHub issue was found.
              </p>
            )}
        </div>
      )}

      {/* Analysis Error */}

      {analysis && !analysis.success && (
        <div
          style={{
            backgroundColor: "#fee2e2",
            border: "1px solid #fecaca",
            padding: "20px",
            borderRadius: "10px",
            marginBottom: "30px",
            color: "#991b1b",
          }}
        >
          <strong>Analysis Failed</strong>

          <p style={{ marginBottom: 0 }}>
            {analysis.error}
          </p>
        </div>
      )}

      {/* GitHub Issues */}

      <h2>GitHub Issues</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "20px",
        }}
      >
        {issues.map((issue) => (
          <div
            key={issue.id}
            style={{
              backgroundColor: "white",
              padding: "20px",
              borderRadius: "10px",
              boxShadow:
                "0 2px 8px rgba(0,0,0,0.08)",
            }}
          >
            <p
              style={{
                color: "#6b7280",
                marginBottom: "8px",
              }}
            >
              Issue #{issue.number}
            </p>

            <h3>{issue.title}</h3>

            <p>
              Status:{" "}
              <strong
                style={{
                  color:
                    issue.state === "open"
                      ? "green"
                      : "#6b7280",
                }}
              >
                {issue.state}
              </strong>
            </p>

            <p>
              Comments: {issue.comments}
            </p>

            <a
              href={issue.html_url}
              target="_blank"
              rel="noreferrer"
              style={{
                color: "#2563eb",
                textDecoration: "none",
                fontWeight: "bold",
              }}
            >
              View on GitHub →
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;