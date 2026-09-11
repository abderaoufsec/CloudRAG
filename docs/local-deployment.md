# Local deployment

From the repository root, after Docker Desktop and Ollama are running:

```powershell
ollama pull qwen3:8b
docker compose config
docker compose up --build -d
docker compose ps
```

The backend runs on port 8000 with `/api/health`; Nginx serves the frontend on
port 8080. The backend reaches Ollama on the Windows host through
`host.docker.internal:11434`.

Useful checks:

```powershell
Invoke-RestMethod http://localhost:8000/api/health
Invoke-WebRequest http://localhost:8080 -UseBasicParsing
docker compose logs --tail=100 backend
```

`docker compose down` stops containers but preserves `./data`. Back up `data`
before manually removing it.
