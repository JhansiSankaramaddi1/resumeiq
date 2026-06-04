"""
ResumeIQ — AI-powered Resume vs Job Description Analyzer
=========================================================
Upload a resume + paste a JD → get:
  • Fit score (0–100)
  • Missing keywords & skills
  • Section-by-section feedback
  • AI-rewritten bullet points (stronger, metric-driven)
  • ATS optimization tips
  • Tailored cover letter opening paragraph
"""
import os, json, re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
import pdfplumber
import docx2txt
import io

app = FastAPI(title="ResumeIQ API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── TEXT EXTRACTION ───────────────────────────────────────────────────────────

def extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    elif filename.endswith(".docx"):
        return docx2txt.process(io.BytesIO(file_bytes))
    else:
        return file_bytes.decode("utf-8", errors="ignore")

# ── PROMPTS ───────────────────────────────────────────────────────────────────

FIT_ANALYSIS_PROMPT = """You are an expert technical recruiter and resume coach with 10+ years experience.
Analyze how well this resume matches the job description.

## Resume:
{resume}

## Job Description:
{jd}

Return a JSON object with this exact structure:
{{
  "fit_score": <integer 0-100>,
  "score_rationale": "2-3 sentence explanation of the score",
  "matched_keywords": ["keyword1", "keyword2", ...],
  "missing_keywords": ["keyword1", "keyword2", ...],
  "missing_skills": ["skill1", "skill2", ...],
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2", "gap3"],
  "ats_tips": ["tip1", "tip2", "tip3"],
  "section_feedback": {{
    "summary": "feedback on professional summary",
    "experience": "feedback on work experience bullets",
    "skills": "feedback on skills section",
    "education": "overall assessment"
  }},
  "overall_recommendation": "STRONG_FIT | GOOD_FIT | WEAK_FIT | NOT_A_FIT"
}}"""

BULLET_REWRITE_PROMPT = """You are an expert resume writer. Rewrite these resume bullet points to be:
1. Action-verb led (strong verbs: Built, Reduced, Led, Designed, Optimized, etc.)
2. Metric-driven (add realistic % improvements, scale, team sizes if missing)
3. Relevant to this job description
4. ATS-friendly (include keywords from the JD naturally)

## Job Description Keywords: {keywords}

## Original Bullets:
{bullets}

Return JSON:
{{
  "rewrites": [
    {{"original": "...", "improved": "...", "changes": "what was improved"}},
    ...
  ]
}}"""

COVER_LETTER_PROMPT = """Write a compelling opening paragraph (3-4 sentences) for a cover letter.
The candidate is applying for: {role} at {company}

Their key strengths relevant to this role: {strengths}
Their years of experience: {years_exp}

Make it specific, confident, and NOT generic. Reference something real about the role or company if possible.
Output only the paragraph text, no labels."""

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    company_name: str = Form(default=""),
    role_title: str = Form(default="")
):
    """Full resume analysis: fit score, gaps, keywords, feedback."""
    resume_bytes = await resume.read()
    resume_text = extract_text(resume_bytes, resume.filename)

    if len(resume_text.strip()) < 100:
        raise HTTPException(400, "Could not extract text from resume. Ensure it's not a scanned image.")
    if len(job_description.strip()) < 100:
        raise HTTPException(400, "Job description is too short. Paste the full JD.")

    # Main analysis
    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": FIT_ANALYSIS_PROMPT.format(
            resume=resume_text[:6000], jd=job_description[:4000]
        )}],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    analysis = json.loads(resp.choices[0].message.content)

    # Extract bullets from resume for rewriting
    bullets = extract_bullets(resume_text)
    keywords_str = ", ".join(analysis.get("missing_keywords", [])[:10])

    rewrite_resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": BULLET_REWRITE_PROMPT.format(
            keywords=keywords_str, bullets="\n".join(bullets[:8])
        )}],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    rewrites = json.loads(rewrite_resp.choices[0].message.content)

    # Cover letter opener
    strengths_str = "; ".join(analysis.get("strengths", [])[:3])
    cover_resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": COVER_LETTER_PROMPT.format(
            role=role_title or "Software Engineer",
            company=company_name or "your company",
            strengths=strengths_str,
            years_exp="5"
        )}],
        temperature=0.7
    )
    cover_letter_opener = cover_resp.choices[0].message.content

    return {
        "fit_score": analysis.get("fit_score", 0),
        "score_rationale": analysis.get("score_rationale", ""),
        "recommendation": analysis.get("overall_recommendation", ""),
        "matched_keywords": analysis.get("matched_keywords", []),
        "missing_keywords": analysis.get("missing_keywords", []),
        "missing_skills": analysis.get("missing_skills", []),
        "strengths": analysis.get("strengths", []),
        "gaps": analysis.get("gaps", []),
        "ats_tips": analysis.get("ats_tips", []),
        "section_feedback": analysis.get("section_feedback", {}),
        "bullet_rewrites": rewrites.get("rewrites", []),
        "cover_letter_opener": cover_letter_opener,
        "resume_length": len(resume_text),
        "jd_length": len(job_description)
    }

@app.post("/score-quick")
async def quick_score(
    resume_text: str = Form(...),
    job_description: str = Form(...)
):
    """Fast fit score only — no rewrites. Returns in ~1 second."""
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Score resume fit for this JD from 0-100.
Resume: {resume_text[:3000]}
JD: {job_description[:2000]}
Return JSON: {{"score": <int>, "top_gaps": ["gap1","gap2","gap3"]}}"""}],
        response_format={"type": "json_object"}, temperature=0
    )
    return json.loads(resp.choices[0].message.content)

@app.post("/rewrite-bullets")
async def rewrite_bullets_endpoint(
    bullets: list[str],
    keywords: list[str],
    role: str = "Software Engineer"
):
    """Rewrite specific bullets to match a role."""
    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": BULLET_REWRITE_PROMPT.format(
            keywords=", ".join(keywords),
            bullets="\n".join(f"• {b}" for b in bullets)
        )}],
        response_format={"type": "json_object"}, temperature=0.3
    )
    return json.loads(resp.choices[0].message.content)

@app.get("/health")
async def health():
    return {"status": "ok", "model": "gpt-4o"}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def extract_bullets(text: str) -> list[str]:
    """Extract bullet-point lines from resume text."""
    lines = text.split("\n")
    bullets = []
    for line in lines:
        line = line.strip()
        if re.match(r'^[•\-\*▪▸→]', line) and len(line) > 30:
            bullets.append(re.sub(r'^[•\-\*▪▸→]\s*', '', line))
        elif re.match(r'^\w{2,}ed\s|^\w{2,}ized\s|^Built|^Led|^Designed|^Developed|^Reduced|^Increased', line):
            if len(line) > 30:
                bullets.append(line)
    return bullets[:15]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)

# ── SERVE DEMO UI ─────────────────────────────────────────────────────────────
from fastapi.responses import HTMLResponse
from pathlib import Path as _Path

@app.get("/", response_class=HTMLResponse)
async def demo_ui():
    html_path = _Path(__file__).parent / "demo.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    return HTMLResponse("<h1>ResumeIQ API</h1><p>See /docs for API reference.</p>")
