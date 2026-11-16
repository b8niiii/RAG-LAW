# Run RAG-LAW with the Italian Civil Code on Cloud Run

The original prototype used the FastAPI service `raglaw2` in `us-central1`. This release keeps SQLite for article and passage text and FAISS for retrieval. Cloud Build creates both files once and includes them with the model in an immutable container image. Cloud Run instances load that prepared index at startup. Each request reads SQLite, and each new revision can carry a different corpus snapshot.

## Prepare the official edition

This repository includes the Civil Code edition as of 15 November 2026 in `examples/civil_code.json.gz`. To refresh it, export the decree in **AKN (Akoma Ntoso)** format from Normattiva Open Data. Search for Royal Decree 262 of 16 March 1942 and choose the edition valid on the date you intend to index. Include the annex with the six books. The importer records the source and date and includes only the Code. [Normattiva Open Data](https://dati.normattiva.it/Come-scaricare-i-dati) · [Civil Code](https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:regio.decreto:1942-03-16;262)

```bash
python -m scripts.civil_code path/to/export.zip \
  --as-of YYYY-MM-DD --output data/civil-code.json
```

To validate the bundled edition locally, build the index and run the API with it. Use a fresh output directory when changing the edition or model.

```bash
python -m scripts.build_index \
  --corpus examples/civil_code.json.gz --output data/civil-code-index
RAGLAW_INDEX_PATH=data/civil-code-index python -m uvicorn api.main:app --port 8000
```

## Build an image without changing live traffic

Set the existing Google Cloud project ID and the name of its Docker repository in Artifact Registry. The build account needs permission to write to that repository, and the deployer needs permission to build the image and update the existing Cloud Run service. [Cloud Run deployment permissions](https://docs.cloud.google.com/run/docs/deploying-source-code) · [Artifact Registry](https://docs.cloud.google.com/artifact-registry/docs/docker)

```bash
export GCP_PROJECT='your-existing-project-id'
export GCP_REGION='us-central1'
export GCP_SERVICE='raglaw2'
export GCP_DOCKER_REPO='your-artifact-registry-repository'

gcloud run services describe "$GCP_SERVICE" --project "$GCP_PROJECT" --region "$GCP_REGION"
```

Continue after `describe` shows the expected service. Stage the committed source and bundled corpus for Cloud Build.

```bash
revision="$(git rev-parse --short=8 HEAD)"
image="$GCP_REGION-docker.pkg.dev/$GCP_PROJECT/$GCP_DOCKER_REPO/rag-law-api:$revision"
release_dir="$(mktemp -d)"

git archive HEAD | tar -x -C "$release_dir"

gcloud builds submit "$release_dir" --project "$GCP_PROJECT" \
  --config "$release_dir/deploy/cloudbuild.yaml" \
  --substitutions "_IMAGE=$image"
```

To build with a newly imported edition, place its JSON in `$release_dir/cloud_input/civil-code.json` and add `,_CORPUS=cloud_input/civil-code.json` to the substitutions string. Use a new image tag for each edition.

Create a tagged revision and leave the existing traffic allocation in place. Use the tagged revision URL printed by Cloud Run for the smoke checks. The service keeps its existing invoker configuration. If it requires authentication, send an identity token from an account allowed to invoke the service. [Cloud Run revisions and traffic](https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration)

```bash
gcloud run deploy "$GCP_SERVICE" --project "$GCP_PROJECT" --region "$GCP_REGION" \
  --image "$image" --no-traffic --tag "verify-$revision"
```

```bash
export VERIFY_URL='https://revision-url-printed-by-cloud-run'
curl -fsS "$VERIFY_URL/health"
curl -fsS "$VERIFY_URL/search" -H 'Content-Type: application/json' \
  -d '{"query":"Quali riparazioni necessarie spettano al locatore durante la locazione?","top_k":5}'
```

Check that `/health` identifies the dated Civil Code corpus and that the search returns Article 1576 with a passage and its full text. Then direct traffic to the verified revision in the Cloud Run console. Use the service URL as `RAGLAW_API_URL` when running Streamlit. Revert to a previous revision from the Cloud Run traffic page if needed.

Normattiva supplies a free, non-authentic reproduction. The indexed edition remains fixed until a new corpus is imported and deployed.
