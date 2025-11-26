FROM python:3.13-slim-trixie

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the project files
COPY . .

# Install dependencies
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 9000

# Run the application directly from the venv (not using uv run)
CMD ["/app/.venv/bin/python", "-m", "app.main"]
