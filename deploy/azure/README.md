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

This deployment demonstrates the CloudRAG architecture on Azure Container Apps. The backend is configured with `LLM_PROVIDER=local` and `VECTOR_STORE=faiss`, but note that:

- **Local Ollama limitation**: The local Ollama provider configuration references `http://localhost:11434`, which will not be available in Azure Container Apps. For a production Azure deployment, you should:
  1. Implement an Azure OpenAI provider and configure `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_DEPLOYMENT` environment variables
  2. Deploy Ollama in a separate container with proper internal networking
  3. Or temporarily set `LLM_PROVIDER=disabled` to run the document processing and retrieval pipeline without the LLM generation step

- **FAISS persistence**: Without `-EnablePersistentStorage`, the FAISS index and SQLite database will be lost when the container app restarts. Use `-EnablePersistentStorage` for state persistence.

Azure Container Apps Consumption can scale to zero, but Azure Container Registry can incur charges. `-EnablePersistentStorage` also creates a Standard_LRS Azure Storage account and Azure Files share, which can incur charges.

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

The script prints the frontend URL. Verify its API separately by opening the printed API URL followed by `/api/health` and `/api/ready`.

Delete all resources when the demonstration is over:

```powershell
az group delete --name cloudragdemo-rg --yes --no-wait
```
