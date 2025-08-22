# Install before running:
# pip install streamlit spacy PyPDF2 python-docx matplotlib reportlab

import streamlit as st
import spacy
import PyPDF2
import docx
import re
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load English NLP model
nlp = spacy.load("en_core_web_sm")

# -------------------------
# Utility Functions
# -------------------------

def extract_text_from_pdf(file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

def extract_keywords(text):
    doc = nlp(text)
    keywords = [token.text for token in doc if token.is_alpha and not token.is_stop]
    return set(keywords)

def match_score(resume_keywords, jd_keywords):
    matched = resume_keywords & jd_keywords
    score = (len(matched) / len(jd_keywords)) * 100 if jd_keywords else 0
    return round(score, 2), matched

def create_pie_chart(matched_count, missing_count):
    labels = ['Matched', 'Missing']
    sizes = [matched_count, missing_count]
    colors = ['#4CAF50', '#F44336']
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')
    return fig

def generate_pdf_report(score, matched_keywords, missing_keywords):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Resume Analysis Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Match Score: {score}%")
    
    c.drawString(50, 690, "Matched Keywords:")
    text = ", ".join(matched_keywords) if matched_keywords else "None"
    c.drawString(60, 675, text)

    c.drawString(50, 645, "Missing Keywords:")
    text = ", ".join(missing_keywords) if missing_keywords else "None"
    c.drawString(60, 630, text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# -------------------------
# Streamlit UI
# -------------------------

st.title("📄 AI-Driven Resume Analyzer (Pro)")
st.write("Upload your resume and paste a job description to see the match score, keyword analysis, and download a PDF report.")

uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
job_description = st.text_area("Paste Job Description Here")

if uploaded_file and job_description:
    # Extract resume text
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = extract_text_from_docx(uploaded_file)
    
    # Clean and extract keywords
    resume_clean = clean_text(resume_text)
    jd_clean = clean_text(job_description)

    resume_keywords = extract_keywords(resume_clean)
    jd_keywords = extract_keywords(jd_clean)

    score, matched_keywords = match_score(resume_keywords, jd_keywords)
    missing_keywords = jd_keywords - resume_keywords

    # Display results
    st.subheader("✅ Match Score")
    st.metric(label="Score (%)", value=score)

    st.subheader("📌 Matched Keywords")
    st.write(", ".join(matched_keywords))

    st.subheader("⚠️ Missing Keywords")
    st.write(", ".join(missing_keywords) if missing_keywords else "None — Great match!")

    # Chart
    st.subheader("📊 Keyword Analysis Chart")
    fig = create_pie_chart(len(matched_keywords), len(missing_keywords))
    st.pyplot(fig)

    # PDF Download
    pdf_buffer = generate_pdf_report(score, matched_keywords, missing_keywords)
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name="resume_analysis_report.pdf",
        mime="application/pdf"
    )
