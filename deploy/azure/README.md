# CloudRAG Azure deployment

## Architecture

```text
Browser
  -> CloudRAG Web (Azure Container Apps / Nginx)
  -> CloudRAG API (Azure Container Apps / FastAPI)
  -> Azure Container Registry (private images, managed identity pull)

Optional: Azure Files mounted at /app/data for SQLite, FAISS, and documents.
```

The API uses a user-assigned managed identity with the least-privilege `AcrPull` role, so registry passwords are never put in source code or Container App secrets.

## Deployment scope and cost

This is Milestone 8 only. It deploys the application architecture, but deliberately sets `LLM_PROVIDER=disabled`; local Ollama is not deployed to Azure and Azure OpenAI belongs in Milestone 9.

Azure Container Apps Consumption can scale to zero, but Azure Container Registry can incur charges. `-EnablePersistentStorage` also creates a Standard_LRS Azure Storage account and Azure Files share, which can incur charges. Persistent storage is required for uploaded documents, SQLite, and FAISS vectors to survive a Container App restart. Without it, the deployment is a temporary smoke-test deployment only.

## One-command deployment

Install the current Azure CLI, sign in to the subscription you intend to use, then run from the project root:

```powershell
.\deploy\azure\deploy.ps1 -ProjectName cloudragdemo -Location westeurope
```

For persistent state, explicitly opt in:

```powershell
.\deploy\azure\deploy.ps1 -ProjectName cloudragdemo -Location westeurope -EnablePersistentStorage
```

The script requires you to type `DEPLOY` before it creates resources. It uses Azure Container Registry cloud builds, so Docker is not required on your PC.

## Verify and remove

The script prints the frontend URL. Verify its API separately by opening the printed API URL followed by `/api/health`.

Delete all resources when the demonstration is over:

```powershell
az group delete --name cloudragdemo-rg --yes --no-wait
```
