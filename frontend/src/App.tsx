import { useState, useCallback } from "react";

const API = "http://localhost:8004";

const SCORE_COLOR = (s: number) =>
  s >= 80 ? "#10b981" : s >= 60 ? "#f59e0b" : s >= 40 ? "#f97316" : "#ef4444";

const Badge = ({ text, color }: { text: string; color: string }) => (
  <span style={{ background: `${color}18`, color, border: `1px solid ${color}40`, borderRadius: 4, padding: "2px 10px", fontSize: 12, fontWeight: 600, marginRight: 6, marginBottom: 6, display: "inline-block" }}>{text}</span>
);

export default function App() {
  const [jd, setJd] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const analyze = async () => {
    if (!file || !jd.trim()) { setError("Upload a resume and paste a JD"); return; }
    setLoading(true); setError(""); setResult(null);
    const fd = new FormData();
    fd.append("resume", file);
    fd.append("job_description", jd);
    fd.append("company_name", company);
    fd.append("role_title", role);
    try {
      const res = await fetch(`${API}/analyze`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const S = { minHeight: "100vh", background: "#0a0b0f", color: "#e2e8f0", fontFamily: "Inter,system-ui,sans-serif", padding: "32px 5%" };
  const card = { background: "#10121a", border: "1px solid #1e2535", borderRadius: 12, padding: 24, marginBottom: 20 };
  const input = { width: "100%", background: "#161926", border: "1px solid #1e2535", borderRadius: 8, padding: "10px 14px", color: "#e2e8f0", fontSize: 14, outline: "none", boxSizing: "border-box" as const };

  return (
    <div style={S}>
      <div style={{ maxWidth: 860, margin: "0 auto" }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, color: "#7c3aed", marginBottom: 4 }}>🎯 ResumeIQ</h1>
        <p style={{ color: "#64748b", marginBottom: 32 }}>AI-powered resume vs job description analyzer · GPT-4o</p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
          <div style={card}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: 600, fontSize: 14 }}>📄 Resume (PDF or DOCX)</label>
            <input type="file" accept=".pdf,.docx,.txt" onChange={e => setFile(e.target.files?.[0] || null)}
              style={{ ...input, cursor: "pointer" }} />
            {file && <div style={{ fontSize: 12, color: "#10b981", marginTop: 8 }}>✓ {file.name}</div>}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={card}><label style={{ display: "block", marginBottom: 8, fontSize: 13, fontWeight: 600 }}>Company</label>
              <input style={input} value={company} onChange={e => setCompany(e.target.value)} placeholder="e.g. Stripe" /></div>
            <div style={card}><label style={{ display: "block", marginBottom: 8, fontSize: 13, fontWeight: 600 }}>Role</label>
              <input style={input} value={role} onChange={e => setRole(e.target.value)} placeholder="e.g. Full Stack Eng" /></div>
          </div>
        </div>

        <div style={card}>
          <label style={{ display: "block", marginBottom: 8, fontWeight: 600, fontSize: 14 }}>📋 Job Description</label>
          <textarea value={jd} onChange={e => setJd(e.target.value)} rows={8}
            placeholder="Paste the full job description here..."
            style={{ ...input, resize: "vertical", lineHeight: 1.6 }} />
        </div>

        {error && <div style={{ background: "#ef444418", border: "1px solid #ef444440", borderRadius: 8, padding: "12px 16px", color: "#f87171", marginBottom: 16, fontSize: 14 }}>{error}</div>}

        <button onClick={analyze} disabled={loading}
          style={{ background: loading ? "#374151" : "#7c3aed", border: "none", borderRadius: 8, padding: "14px 32px", color: "white", fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", width: "100%" }}>
          {loading ? "⏳ Analyzing with GPT-4o (15–30s)..." : "🔍 Analyze Resume"}
        </button>

        {result && (
          <div style={{ marginTop: 32 }}>
            {/* Score */}
            <div style={{ ...card, display: "flex", alignItems: "center", gap: 32, background: "#0f172a" }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 64, fontWeight: 800, color: SCORE_COLOR(result.fit_score), lineHeight: 1 }}>{result.fit_score}</div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>FIT SCORE</div>
              </div>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color: SCORE_COLOR(result.fit_score), marginBottom: 8 }}>{result.recommendation?.replace(/_/g, " ")}</div>
                <div style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.6 }}>{result.score_rationale}</div>
              </div>
            </div>

            {/* Keywords */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
              <div style={card}>
                <div style={{ fontWeight: 700, marginBottom: 12, color: "#10b981" }}>✅ Matched Keywords</div>
                {result.matched_keywords?.map((k: string) => <Badge key={k} text={k} color="#10b981" />)}
              </div>
              <div style={card}>
                <div style={{ fontWeight: 700, marginBottom: 12, color: "#ef4444" }}>❌ Missing Keywords</div>
                {result.missing_keywords?.map((k: string) => <Badge key={k} text={k} color="#ef4444" />)}
                {result.missing_skills?.map((k: string) => <Badge key={k} text={k} color="#f97316" />)}
              </div>
            </div>

            {/* Bullet Rewrites */}
            {result.bullet_rewrites?.length > 0 && (
              <div style={card}>
                <div style={{ fontWeight: 700, marginBottom: 16, fontSize: 16 }}>✍️ Bullet Point Rewrites</div>
                {result.bullet_rewrites.map((r: any, i: number) => (
                  <div key={i} style={{ borderBottom: "1px solid #1e2535", paddingBottom: 16, marginBottom: 16 }}>
                    <div style={{ color: "#ef4444", fontSize: 13, marginBottom: 6 }}>Before: {r.original}</div>
                    <div style={{ color: "#10b981", fontSize: 13, marginBottom: 4 }}>After: {r.improved}</div>
                    <div style={{ color: "#64748b", fontSize: 11 }}>💡 {r.changes}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Cover Letter */}
            {result.cover_letter_opener && (
              <div style={card}>
                <div style={{ fontWeight: 700, marginBottom: 12, fontSize: 16 }}>✉️ Cover Letter Opener</div>
                <div style={{ color: "#94a3b8", lineHeight: 1.7, fontStyle: "italic", borderLeft: "3px solid #7c3aed", paddingLeft: 16 }}>{result.cover_letter_opener}</div>
              </div>
            )}

            {/* ATS Tips */}
            <div style={card}>
              <div style={{ fontWeight: 700, marginBottom: 12, fontSize: 16 }}>🤖 ATS Optimization Tips</div>
              {result.ats_tips?.map((t: string, i: number) => (
                <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8, fontSize: 14, color: "#94a3b8" }}>
                  <span style={{ color: "#7c3aed" }}>▸</span> {t}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
