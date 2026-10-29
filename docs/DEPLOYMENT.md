# AWS deployment guide

No AWS deployment was attempted and no paid resources were created. The images and local Compose workflow are tested separately from cloud operations. Obtain approval for the account, region and budget before running resource-creation commands.

## Architecture matched to this implementation

For a first controlled pilot, use one EC2 host running the two app containers behind an Application Load Balancer with HTTPS, private RDS PostgreSQL, and an encrypted persistent EBS volume mounted for uploads and model checkpoints. This matches the implemented local storage adapter. Use Systems Manager Session Manager rather than exposing SSH. Keep the EC2 application in a private subnet if the approved network provides the required egress/VPC endpoints.

Choose the instance size only after measuring the selected trained checkpoint, concurrency and upload workload on the target CPU architecture. Synthetic test latency is not evidence of production capacity. Begin a benchmark in an explicitly approved temporary environment; measure RSS, p95 latency, simultaneous requests and failure behavior. One inference worker is the current default. GPU deployment needs a CUDA image and target-device benchmarking; it is not provided by the CPU image.

For high availability, implement private S3 storage or a properly managed shared filesystem before adding backend replicas. A local Docker upload volume cannot safely act as shared multi-host storage. An ECS/Fargate + RDS + S3 deployment is a future scaling path, not an already configured integration. Add a distributed rate limiter or AWS WAF; the in-process limiter is only appropriate to the single-worker pilot.

## Network and secrets

- ALB security group: inbound 443 from approved clients/the internet as intended; optional 80 solely to redirect to HTTPS.
- App security group: port 8080 only from the ALB security group. Do not expose 8000 or 5432.
- DB security group: 5432 only from the app security group, RDS publicly accessible **No**.
- Use private DB subnet groups, encryption at rest, TLS database connections (`sslmode=require` at minimum; verify the RDS CA for production), automated backups and deletion protection.
- Place DB credentials and any weather key in Secrets Manager or SSM Parameter Store. Inject at runtime via a narrowly scoped instance role; never bake secrets into images or frontend variables.
- Use ACM certificate validation and an HTTPS ALB listener; Route 53 alias (or DNS provider record) points the selected domain to the ALB. Configure the exact HTTPS origin in `CORS_ORIGINS`.
- Limit outbound traffic to needed package/container endpoints during deployment, the weather provider, RDS and logging/secrets endpoints. Private subnets may incur NAT/endpoint costs; budget explicitly.

## Build and publish images (after approval)

Install/configure AWS CLI v2 with an authorized profile; use the intended account and region. These commands create repositories and upload images, so execute only after approval. Replace the variables with real approved values.

```sh
export AWS_REGION=YOUR_APPROVED_REGION
export CANOPY_ACCOUNT_ID=YOUR_ACCOUNT_ID
export CANOPY_TAG=YOUR_RELEASE_TAG
export CANOPY_REGISTRY="$CANOPY_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
aws sts get-caller-identity
aws ecr create-repository --repository-name canopy-backend --region "$AWS_REGION" --image-scanning-configuration scanOnPush=true
aws ecr create-repository --repository-name canopy-frontend --region "$AWS_REGION" --image-scanning-configuration scanOnPush=true
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$CANOPY_REGISTRY"
# Match platform to the selected host. Use linux/arm64 for Graviton.
docker buildx build --platform linux/amd64 -f backend/Dockerfile -t "$CANOPY_REGISTRY/canopy-backend:$CANOPY_TAG" --push .
docker buildx build --platform linux/amd64 -f frontend/Dockerfile -t "$CANOPY_REGISTRY/canopy-frontend:$CANOPY_TAG" --push .
```

Official reference: https://docs.aws.amazon.com/cli/latest/reference/ecr/get-login-password.html . Pin verified image digests for production rollback after scanning.

## On the approved EC2 host

Provision an encrypted EBS data directory owned by container UID 1000 (verify with the built image). Store `selected.pt` under `/srv/canopy/models/`; store uploads under `/srv/canopy/uploads/`. Keep backups separate. Set `CANOPY_BACKEND_IMAGE`, `CANOPY_FRONTEND_IMAGE`, `DATABASE_URL`, `CORS_ORIGINS` and other settings in a mode-600 environment file sourced from your secret provider. The database URL must reference RDS, not the local Compose service. Do not print it in logs.

```sh
# From the project directory on the host, after injecting environment values:
docker compose -f deploy/compose.aws.yml pull
docker compose -f deploy/compose.aws.yml run --rm migrate
docker compose -f deploy/compose.aws.yml up -d backend frontend
curl --fail http://127.0.0.1:8080/api/health
```

Register the EC2 host in the ALB target group on port 8080, health path `/api/health`, success code 200. The supplied cloud Compose file publishes 8080 on the host; its security group must restrict access to the ALB. Log in through the HTTPS domain, create a field, upload an image, download a report and restart the app to confirm persistence. The Python app does not trust forwarded headers by default; if configuring real-client rate limiting, establish a strict trusted-proxy chain first.

Deployment acceptance requires actual RDS migration, HTTPS, authorization, upload persistence, restored backup checks and trained-checkpoint latency on the chosen host. None of those cloud checks can be substituted with a successful local build.

## Backups and restore

Local development snapshot:

```sh
mkdir -p backups
docker compose exec -T db pg_dump -U canopy -d canopy -Fc > backups/canopy.dump
# Back up the uploads volume with the application quiesced or using a consistent snapshot.
```

For RDS, enable automated backup retention according to the agreed recovery objective, take a snapshot before migrations, and periodically restore to a separate private instance. Verify the target VPC/subnet/security groups rather than accepting defaults. Back up the upload EBS volume and model artifact/configuration consistently with DB state. Encrypt backups and restrict IAM access. A database backup alone cannot recover leaf images.

Restore rehearsal: provision an isolated DB, restore the dump/snapshot, restore corresponding upload/model files, run migrations only if required for the restored version, then verify account access, scan/image links and report downloads. Cut over by updating the secret-backed DB connection only after validation. Never test restores destructively against the live database.

Official references: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_RestoreFromSnapshot.html and https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.RDSSecurityGroups.html .

## Information needed for real deployment

Approved AWS account/profile, region, spend limit, intended users/traffic, domain/DNS authority, selected model checkpoint and benchmark results, backup retention and privacy requirements. Credentials should be configured locally through the standard AWS credential chain, not pasted into chat.
