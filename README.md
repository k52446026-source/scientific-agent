# 🧪 Scientific Agent

> Мой первый ИИ-агент для ускорения научного обзора.  
> 🔍 Ищет статьи на arXiv → 🧠 кратко пересказывает → 📚 сохраняет в удобном формате.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-optional-green?logo=ollama)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✅ Возможности
- Работает **на любом компьютере** (Windows/macOS/Linux)
- Без GPU, без регистрации (базовый режим)
- С Ollama → суммаризация через `phi3` (локально)
- С Groq API → суммаризация через `llama3-8b` (бесплатно)

## ▶️ Как запустить

### Быстро (без ИИ)
```bash
git clone https://github.com/ваш-логин/scientific-agent.git
cd scientific-agent
python -m venv venv
venv\Scripts\activate
pip install arxiv rich
python arxiv_summarizer.py