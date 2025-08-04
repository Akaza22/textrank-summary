from flask import Flask, request, jsonify
import requests
from io import BytesIO
from pdfminer.high_level import extract_text
import re

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

app = Flask(__name__)

# 🧼 Text cleaner agar input ke TextRank lebih bersih
def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)                      # gabungkan spasi berlebih
    text = re.sub(r'\[[0-9]+\]', '', text)                # hilangkan referensi seperti [1]
    text = re.sub(r'(?<=\w)- (?=\w)', '', text)           # gabungkan kata yang di-break dengan tanda minus
    text = re.sub(r'\n+', '\n', text)                     # ganti banyak newline jadi satu
    return text.strip()

# 🧠 Ringkasan pakai TextRank
def summarize_text_textrank(text, num_sentences=5):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return " ".join(str(sentence) for sentence in summary)

@app.route('/summarize-url', methods=['POST'])
def summarize_from_url():
    data = request.get_json()
    url = data.get('url')
    num_sentences = data.get('sentences', 5)

    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    try:
        # Ambil PDF dari URL Cloudinary
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch PDF'}), 400

        pdf_file = BytesIO(response.content)

        # 🧾 Ekstraksi teks full dengan pdfminer
        raw_text = extract_text(pdf_file)
        cleaned_text = clean_text(raw_text)

        if not cleaned_text.strip():
            return jsonify({'error': 'No meaningful text found in PDF'}), 400

        summary = summarize_text_textrank(cleaned_text, num_sentences)
        return jsonify({'summary': summary})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel handler
def handler(request, response):
    return app(request.scope, request.receive, request.send)
