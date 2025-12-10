# # arxiv_summarizer.py
import arxiv
import time
import random
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

def search_arxiv(query: str, max_results: int = 3, delay: float = 1.5):
    """Ищет статьи на arXiv с защитой от 503 ошибок."""
    console.print(f"🔍 Запрашиваю arXiv по: [bold]{query}[/bold]...")
    
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    client = arxiv.Client(
        page_size=10,        # ← критически важно!
        delay_seconds=delay,
        num_retries=3
    )
    
    try:
        results = []
        for i, result in enumerate(client.results(search)):
            if i >= max_results:
                break
            results.append(result)
            time.sleep(random.uniform(0.5, 1.2))
        return results
    
    except arxiv.HTTPError as e:
        rprint(f"[red]❌ arXiv вернул ошибку: HTTP {e.status_code}[/red]")
        rprint(f"[yellow]💡 Советы:[/yellow]")
        rprint("  • Подождите 1–2 минуты и повторите")
        rprint("  • Используйте более конкретный запрос (напр.: 'LLM agents robotics')")
        rprint("  • Избегайте частых запусков")
        return []
    except Exception as e:
        rprint(f"[red]⚠️ Ошибка: {type(e).__name__}: {e}[/red]")
        return []

def display_results(results):
    if not results:
        console.print("[bold yellow]📭 Ничего не найдено — попробуйте другой запрос.[/bold yellow]")
        return

    table = Table(title="📄 Найдено на arXiv (последние)", show_lines=True)
    table.add_column("№", style="cyan", justify="right", width=2)
    table.add_column("Заголовок", style="magenta", overflow="fold")
    table.add_column("Авторы", style="green", overflow="fold")
    table.add_column("Дата", style="yellow", width=10)

    for i, paper in enumerate(results, 1):
        authors = ", ".join([a.name.split()[-1] for a in paper.authors[:3]])
        if len(paper.authors) > 3:
            authors += " + др."
        table.add_row(
            str(i),
            paper.title,
            authors,
            paper.published.strftime("%Y-%m-%d")
        )
    console.print(table) 

def save_to_markdown(results, filename="papers.md"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 📚 Мои научные находки\n\n")
        if not results:
            f.write("> Пока ничего не найдено. Попробуйте уточнить запрос!\n")
            return
        for i, paper in enumerate(results, 1):
            f.write(f"## {i}. {paper.title}\n")
            f.write(f"- **Авторы**: {', '.join(a.name for a in paper.authors)}\n")
            f.write(f"- **Дата**: {paper.published.date()}\n")
            f.write(f"- **Ссылка**: [Читать на arXiv]({paper.entry_id}) | [PDF]({paper.pdf_url})\n")
            summary = paper.summary.replace('\n', ' ').strip()
            f.write(f"- **Аннотация**:\n  > {summary[:400]}{'...' if len(summary) > 400 else ''}\n\n")
    console.print(f"✅ Сохранено в [bold green]{filename}[/bold green]")

def save_to_json(results, filename="papers.json"):
    """Сохраняет результаты в JSON — для программной обработки (агентов, БД и т.д.)"""
    data = []
    for paper in results:
        data.append({
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "published": paper.published.isoformat(),
            "entry_id": paper.entry_id,
            "pdf_url": paper.pdf_url,
            "summary": paper.summary.replace('\n', ' ').strip(),
            "primary_category": paper.primary_category,
            "categories": list(paper.categories),
        })
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    console.print(f"✅ Сохранено в [bold cyan]{filename}[/bold cyan]")

# ======================
# Основной запуск
# ======================
if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold blue]🔬 Научный Ассистент v0.3\n"
        "Теперь с Markdown + JSON-экспортом и защитой от ошибок![/bold blue]",
        title="🤖 Привет, исследователь!",
        border_style="blue"
    ))

    query = input("🔍 Введите тему (на английском, например: 'LLM agents' или 'soft robotics'): ").strip()
    
    if not query:
        query = "AI for open science"
        console.print(f"[yellow]→ Выбрана тема по умолчанию: '{query}'[/yellow]")

    console.rule(f"Запрос: {query}")
    results = search_arxiv(query, max_results=3)
    display_results(results)
    
    # Сохраняем в Markdown всегда
    save_to_markdown(results)

    # Спрашиваем про JSON — только если есть результаты
    if results:
        console.print()
        json_choice = input("💾 Сохранить данные в JSON для дальнейшего анализа? (y/n): ").strip().lower()
        if json_choice in ('y', 'yes', 'д', 'да'):
            save_to_json(results)
        else:
            console.print("[dim]→ Пропускаем JSON.[/dim]")
    
    console.print("\n🚀 Готово! Что дальше?")
    console.print("  • Изучи `papers.md` — там структурированный обзор")
    console.print("  • Если есть `papers.json` — это топливо для ИИ-агента 🪄") 
    console.print("  • Следующий шаг: суммаризация через LLM (ждёшь неделю 2?)")