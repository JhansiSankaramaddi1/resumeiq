# 🎯 ResumeIQ — AI Resume vs Job Description Analyzer

Upload your resume + paste any job description → get an instant fit score, missing keywords, rewritten bullets, and a tailored cover letter opener.

## 🚀 Features
- **Fit Score (0–100)** with detailed rationale — how well your resume matches the JD
- **Missing keywords & skills** — exactly what recruiters and ATS systems are looking for
- **AI bullet rewrites** — transforms weak bullets into metric-driven, action-verb-led statements
- **ATS optimization tips** — format and content suggestions for automated screening
- **Section feedback** — summary, experience, skills, education
- **Cover letter opener** — tailored to the specific role and company
- **Quick score endpoint** — sub-second fit score for batch checking multiple JDs

## 🛠 Tech Stack
| Layer | Tech |
|---|---|
| API | FastAPI + Python async |
| LLM | GPT-4o (analysis) + GPT-4o-mini (quick score) |
| PDF Parsing | pdfplumber |
| DOCX Parsing | docx2txt |
| Output | Structured JSON via response_format |

## ⚡ Quick Start
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python main.py
```

## 📡 API
```bash
# Full analysis
curl -X POST http://localhost:8004/analyze \
  -F "resume=@my_resume.pdf" \
  -F "job_description=We are looking for a Full Stack Engineer..." \
  -F "company_name=Stripe" \
  -F "role_title=Full Stack Engineer"

# Quick score (fast)
curl -X POST http://localhost:8004/score-quick \
  -F "resume_text=John Doe, Software Engineer..." \
  -F "job_description=We are looking for..."
```

## 📊 Sample Output
```json
{
  "fit_score": 74,
  "recommendation": "GOOD_FIT",
  "missing_keywords": ["Kubernetes", "GraphQL", "Redis"],
  "bullet_rewrites": [
    {
      "original": "Worked on backend APIs",
      "improved": "Designed and built 12 REST APIs serving 500K daily requests, reducing p99 latency by 35%",
      "changes": "Added metrics, scale, and specific tech"
    }
  ]
}
```
