# arxiv_summarizer.py — v0.5: Универсальный агент (работает ВЕЗДЕ)
from dotenv import load_dotenv
load_dotenv()  # ← эта строка загружает переменные из .env
import arxiv
import time
import random
import json
import os
import subprocess
import sys
import requests
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# =============== Суммаризация: цепочка попыток ===============
def summarize_paper(text: str) -> str:
    """Суммирует текст — пробует phi3 → Groq → fallback."""
    
    # Попытка 1: phi3 (локально)
    phi3_summary = _try_phi3(text)
    if phi3_summary:
        return f"[phi3] {phi3_summary}"
    
    # Попытка 2: Groq (облако, бесплатно)
    groq_summary = _try_groq(text)
    if groq_summary:
        return f"[Groq] {groq_summary}"
    
    # Попытка 3: fallback (без ИИ)
    return f"[basic] {_fallback_summary(text)}"

def _try_phi3(text: str, max_chars: int = 800) -> str | None:
    try:
        import ollama
        input_text = text[:max_chars] + ("..." if len(text) > max_chars else "")
        prompt = f"""Summarize in 2 sentences. Focus on goal & result. Plain language.

Abstract:
{input_text}

Summary:"""
        
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
            task = progress.add_task("🧠 phi3...", total=None)
            response = ollama.generate(
                model="phi3",
                prompt=prompt,
                options={"temperature": 0.3}
            )
        summary = response["response"].strip()
        if summary.lower().startswith(("summary:", "answer:", "here")):
            summary = summary.split(":", 1)[-1].strip()
        return summary if summary and len(summary) > 20 else None
    except:
        return None

def _try_groq(text: str) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": f"2 предложения: {text[:1000]}"}],
                "temperature": 0.3
            },
            timeout=8
        )
        if resp.status_code == 200:
            out = resp.json()["choices"][0]["message"]["content"].strip()
            return out if len(out) > 20 else None
    except:
        pass
    return None

def _fallback_summary(text: str) -> str:
    clean = text.replace('\n', ' ').strip()
    sentences = [s.strip() for s in clean.split('.') if s.strip()]
    short = '. '.join(sentences[:2]) + ('.' if len(sentences) > 2 else '')
    return short[:350] + "…" if len(short) > 350 else short

# =============== arXiv поиск ===============
def search_arxiv(query: str, max_results: int = 3):
    console.print(f"🔍 Ищу на arXiv: [bold]{query}[/bold]...")
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate)
    client = arxiv.Client(page_size=10, delay_seconds=1.5, num_retries=2)
    try:
        return list(client.results(search))[:max_results]
    except:
        return []

# =============== Вывод и сохранение ===============
def display_results(results):
    if not results:
        console.print("[yellow]📭 Ничего не найдено.[/yellow]")
        return
    table = Table(title="📄 Результаты", show_lines=True)
    table.add_column("№", style="cyan", justify="right", width=2)
    table.add_column("Заголовок", style="magenta", overflow="fold")
    table.add_column("Кратко", style="blue", overflow="fold")
    for i, p in enumerate(results, 1):
        short = getattr(p, 'short_summary', '...')
        table.add_row(str(i), p.title[:60], short[:70] + "..." if len(short) > 70 else short)
    console.print(table)

def save_to_markdown(results, filename="papers.md"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 📚 Научные находки\n\n")
        if not results:
            f.write("> Пусто. Попробуйте другой запрос.\n")
            return
        for i, p in enumerate(results, 1):
            f.write(f"## {i}. {p.title}\n")
            f.write(f"- **Авторы**: {', '.join(a.name for a in p.authors)}\n")
            f.write(f"- **Дата**: {p.published.date()}\n")
            f.write(f"- **Ссылка**: [arXiv]({p.entry_id}) | [PDF]({p.pdf_url})\n")
            f.write(f"\n### 🧠 Кратко:\n> {p.short_summary}\n\n")
            f.write(f"### 📝 Оригинал:\n> {p.summary[:400]}{'...' if len(p.summary) > 400 else ''}\n\n")
    console.print(f"✅ Сохранено: [green]{filename}[/green]")

def save_to_json(results, filename="papers.json"):
    data = [{
        "title": p.title,
        "authors": [a.name for a in p.authors],
        "published": p.published.isoformat(),
        "entry_id": p.entry_id,
        "pdf_url": p.pdf_url,
        "summary_original": p.summary.replace('\n',' ').strip(),
        "summary_ai": p.short_summary
    } for p in results]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    console.print(f"✅ Сохранено: [cyan]{filename}[/cyan]")

# =============== Запуск ===============
if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold blue]🤖 Научный Агент v0.5\n"
        "Работает ВЕЗДЕ: с Ollama, с Groq или без ИИ[/bold blue]\n"
        "[dim]💡 Совет: установите Ollama для лучшей суммаризации → https://ollama.com[/dim]",
        title="🚀 Готов к работе!",
        border_style="blue"
    ))

    query = input("🔍 Тема (напр. 'LLM agents'): ").strip()
    if not query:
        query = "AI for open science"

    console.rule(f"Поиск: {query}")
    results = search_arxiv(query, max_results=2)

    if results:
        console.print("🧠 Суммаризация...")
        for i, paper in enumerate(results, 1):
            console.print(f"  {i}/{len(results)}")
            paper.short_summary = summarize_paper(paper.summary)
    else:
        console.print("[yellow]→ Пропускаем суммаризацию.[/yellow]")

    display_results(results)
    save_to_markdown(results)

    if results and input("\n💾 Сохранить в JSON? (y/n): ").lower() in "yд":
        save_to_json(results)

    console.print("\n🎉 Готово!")
    console.print("  • Откройте `papers.md` — там краткие выводы")
    console.print("  • Чтобы улучшить качество: установите Ollama или добавьте GROQ_API_KEY")