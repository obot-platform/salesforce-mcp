FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the project files
COPY . .

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 9000

# Run the application
CMD ["uv", "run", "python", "-m", "app.main"]