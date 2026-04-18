FROM --platform=linux/amd64 python:3.13-slim AS compile-image

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc rustc cargo \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM --platform=linux/amd64 python:3.13-slim AS run-image

COPY --from=compile-image /root/.local /root/.local

WORKDIR /usr/

# Only the bot
COPY ./src/controllers/bot ./src/controllers/bot

# Other domain & service stuff
COPY ./src/interfaces ./src/interfaces
COPY ./src/models ./src/models
COPY ./src/services ./src/services
COPY ./src/settings.py ./src/settings.py

# Runner
COPY scripts/run_bot.py ./run_bot.py

ENV PYTHONUNBUFFERED=1 PATH=/root/.local/bin:$PATH
CMD ["python3", "run_bot.py"]