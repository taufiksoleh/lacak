FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY backend/data ./data
# Editable install: kode dijalankan dari /app/backend agar data/ dan frontend/dist ditemukan
RUN pip install --no-cache-dir -e .
COPY --from=frontend /app/frontend/dist /app/frontend/dist
ENV DATABASE_URL=sqlite:////data/lacak.db
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
