FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py state.py telegram_source.py ./

RUN useradd -m -u 1000 botuser
USER botuser

CMD ["python", "bot.py"]
