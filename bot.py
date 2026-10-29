
import asyncio
import base64
import os
import re
import sqlite3
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

BASE_DIR = Path(__file__).resolve().parent
FILES_DIR = BASE_DIR / "arquivos"
DB_PATH = BASE_DIR / "estudos.db"
TZ = ZoneInfo("America/Sao_Paulo")
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

FILES_DIR.mkdir(exist_ok=True)

if not BOT_TOKEN:
    raise RuntimeError("Configure TELEGRAM_BOT_TOKEN no .env")

ai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


from contextlib import contextmanager


@contextmanager
def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                summary TEXT NOT NULL,
                original TEXT,
                file_id TEXT,
                file_path TEXT,
                url TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pendente'
            )
        """)


def remember_user(chat_id, user_id):
    with connect_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO users (chat_id, user_id)
               VALUES (?, ?)""",
            (chat_id, user_id),
        )


def save_exercise(chat_id, title, subject, summary,
                  original="", file_id=None, file_path=None, url=None):
    with connect_db() as conn:
        cur = conn.execute("""
            INSERT INTO exercises
            (chat_id, title, subject, summary, original,
             file_id, file_path, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id, title, subject, summary, original,
            file_id, file_path, url,
            __import__("datetime").datetime.now(TZ).isoformat()
        ))
        return cur.lastrowid


def get_pending(chat_id):
    with connect_db() as conn:
        return conn.execute("""
            SELECT * FROM exercises
            WHERE chat_id = ? AND status = 'pendente'
            ORDER BY id
        """, (chat_id,)).fetchall()


def classify_with_ai(kind, text="", path=None, filename=""):
    """Executa a análise da IA. É chamada fora do event loop."""
    if not ai:
        return (
            "Material recebido",
            "A classificar",
            text[:500] or f"Arquivo recebido: {filename}",
        )

    instruction = """
    Você é um assistente de organização de estudos.
    Analise o material e responda em português brasileiro.
    Não resolva o exercício: apenas organize-o.
    Se não souber a matéria, escreva 'Não identificada'.
    Responda exatamente neste formato:
    TÍTULO: título curto
    MATÉRIA: nome da disciplina
    RESUMO: descrição breve do que estudar ou fazer.
    Não invente informações que não aparecem no material.
    """

    content = [{"type": "input_text", "text": instruction}]

    if path and path.suffix.lower() == ".pdf":
        data = base64.b64encode(path.read_bytes()).decode("utf-8")
        content.append({
            "type": "input_file",
            "filename": filename or path.name,
            "file_data": f"data:application/pdf;base64,{data}",
        })
    elif path and path.suffix.lower() in {
        ".jpg", ".jpeg", ".png", ".webp"
    }:
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }[path.suffix.lower()]
        data = base64.b64encode(path.read_bytes()).decode("utf-8")
        content.append({
            "type": "input_image",
            "image_url": f"data:{mime};base64,{data}",
        })
    else:
        content.append({
            "type": "input_text",
            "text": text or f"Arquivo recebido: {filename}",
        })

    response = ai.responses.create(
        model=MODEL,
        input=[{"role": "user", "content": content}],
    )
    result = response.output_text

    def field(name, default):
        match = re.search(
            rf"^{name}:\s*(.+)$",
            result,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        return match.group(1).strip() if match else default

    return (
        field("TÍTULO", "Material recebido"),
        field("MATÉRIA", "Não identificada"),
        field("RESUMO", result[:1000]),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    remember_user(chat.id, user.id)

    await update.message.reply_text(
        "📚 Teu assistente de estudos está pronto!\n\n"
        "Envie texto, fotos, PDFs ou links para salvar.\n\n"
        "/pendentes — ver exercícios em aberto\n"
        "/feito ID — concluir um exercício\n"
        "/ajuda — ver os comandos\n\n"
        "Te lembrarei de estudar de segunda a sexta, às 20h."
    )


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Como usar:\n"
        "• Envie uma questão em texto.\n"
        "• Envie uma foto ou PDF.\n"
        "• Envie um link com https://\n"
        "• /pendentes para ver a lista.\n"
        "• /feito 3 para concluir o exercício 3.\n\n"
        "A IA tenta identificar a matéria e resumir "
        "o material sem resolver a questão."
    )


async def process_material(update, context, kind, text="",
                           file_id=None, filename=""):
    chat_id = update.effective_chat.id
    remember_user(chat_id, update.effective_user.id)

    path = None
    saved_file_id = file_id

    if file_id:
        tg_file = await context.bot.get_file(file_id)

        if tg_file.file_size and tg_file.file_size > MAX_FILE_SIZE:
            await update.effective_message.reply_text(
                "Arquivo acima de 15 MB. Envie uma versão menor."
            )
            return

        safe_name = Path(filename or f"material_{kind}").name
        path = FILES_DIR / f"{chat_id}_{tg_file.file_unique_id}_{safe_name}"
        await tg_file.download_to_drive(custom_path=str(path))

    url_match = re.search(r"https?://\S+", text)
    url = url_match.group(0).rstrip(".,)") if url_match else None

    # A IA só analisa PDFs e imagens nesta primeira versão.
    # Outros documentos são guardados pelo nome.
    if path and path.suffix.lower() not in {
        ".pdf", ".jpg", ".jpeg", ".png", ".webp"
    }:
        title = filename or "Documento recebido"
        subject = "A classificar"
        summary = "Arquivo guardado. Leitura automática não habilitada para este formato."
    else:
        try:
            title, subject, summary = await asyncio.to_thread(
                classify_with_ai, kind, text, path, filename
            )
        except Exception as exc:
            print("Erro na análise da IA:", repr(exc))
            title = filename or text[:70] or "Material recebido"
            subject = "A classificar"
            summary = "Salvo sem análise da IA. Consulte o material original."

    exercise_id = save_exercise(
        chat_id, title, subject, summary,
        original=text, file_id=saved_file_id,
        file_path=str(path) if path else None, url=url,
    )

    await update.effective_message.reply_text(
        f"✅ Exercício #{exercise_id} salvo!\n\n"
        f"📘 Matéria: {subject}\n"
        f"📝 {title}\n"
        f"Resumo: {summary}\n\n"
        f"Às 20h ele aparecerá no teu lembrete."
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_material(
        update, context, "text",
        text=update.message.text,
    )


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    await process_material(
        update, context, "image",
        text=update.message.caption or "",
        file_id=photo.file_id,
        filename=f"{photo.file_unique_id}.jpg",
    )


async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    filename = Path(doc.file_name or "documento").name

    await process_material(
        update, context, "document",
        text=update.message.caption or "",
        file_id=doc.file_id,
        filename=filename,
    )


async def pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_pending(update.effective_chat.id)

    if not rows:
        await update.message.reply_text("🎉 Não há exercícios pendentes!")
        return

    lines = ["📚 Teus exercícios pendentes:\n"]
    for row in rows:
        lines.append(
            f"#{row['id']} — {row['title']}\n"
            f"Matéria: {row['subject']}\n"
            f"{row['summary']}\n"
        )

    message = "\n".join(lines)
    # Telegram limita o tamanho de uma mensagem.
    for i in range(0, len(message), 3500):
        await update.message.reply_text(message[i:i + 3500])


async def feito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Use: /feito 3")
        return

    exercise_id = int(context.args[0])
    with connect_db() as conn:
        cur = conn.execute("""
            UPDATE exercises SET status = 'feito'
            WHERE id = ? AND chat_id = ? AND status = 'pendente'
        """, (exercise_id, update.effective_chat.id))

    if cur.rowcount:
        await update.message.reply_text(
            f"✅ Exercício #{exercise_id} concluído. Boa!"
        )
    else:
        await update.message.reply_text(
            "Não encontrei esse exercício pendente."
        )


async def reminder(context: ContextTypes.DEFAULT_TYPE):
    with connect_db() as conn:
        users = conn.execute("SELECT chat_id FROM users").fetchall()

    for user in users:
        chat_id = user["chat_id"]
        rows = get_pending(chat_id)

        if not rows:
            message = "🌙 Sem exercícios pendentes hoje. Bom descanso!"
        else:
            lines = ["📚 Hora de estudar! Aqui está tua lista:\n"]
            for row in rows[:15]:
                lines.append(
                    f"• #{row['id']} — {row['title']}\n"
                    f"  {row['subject']}\n"
                    f"  /feito {row['id']}\n"
                )
            if len(rows) > 15:
                lines.append(f"... e mais {len(rows) - 15} exercícios.")
            message = "\n".join(lines)

        try:
            await context.bot.send_message(
                chat_id=chat_id, text=message
            )
        except Exception as exc:
            print(f"Falha ao enviar lembrete para {chat_id}: {exc}")


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("pendentes", pendentes))
    app.add_handler(CommandHandler("feito", feito))

    app.add_handler(MessageHandler(
        filters.PHOTO, on_photo
    ))
    app.add_handler(MessageHandler(
        filters.Document.ALL, on_document
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, on_text
    ))

    app.job_queue.run_daily(
        reminder,
        time=time(hour=20, minute=0, tzinfo=TZ),
        days=(1, 2, 3, 4, 5),
        name="lembrete_estudos",
    )

    print("Bot iniciado. Pressione Ctrl+C para encerrar.")
    app.run_polling()


if __name__ == "__main__":
    main()
