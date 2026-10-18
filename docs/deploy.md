> Optional AWS example, unexecuted for the local demo. Local startup requires no cloud credentials. AWS apply requires separate authorization and spending approval.

# Deploy and operate the demo

## Prerequisites owned by the AWS account administrator

Use a dedicated demo account if possible. Choose a region supporting Python 3.12 Lambda. Approve usage charges before creating resources. Set an AWS Budget alert at an agreed amount; an alert is not a hard spending limit. Public API traffic, Lambda execution, logs, and S3 can incur charges. There is no promise of a free deployment.

The `bootstrap/` root automates the state bucket, encryption, versioning, public-access block, TLS-only bucket policy, OIDC trust, and deployment role described below. It must run once through an approved administrator session, never through the application deployment role. No credentials are needed in files. Review the plan before applying:

```sh
terraform -chdir=bootstrap init
terraform -chdir=bootstrap plan -var="state_bucket_name=YOUR_UNIQUE_BUCKET" -var="region=YOUR_REGION" -out=bootstrap.tfplan
terraform -chdir=bootstrap apply bootstrap.tfplan
```

If the account already has GitHub OIDC, pass `-var="existing_oidc_provider_arn=YOUR_PROVIDER_ARN"` to the plan. Back up bootstrap state securely; it stays local until explicitly migrated. This bootstrap has been validated offline, not applied to AWS. It can create/modify the named runtime role and all HTTP APIs in the selected region; use a dedicated demo account and review/tighten those permissions. The main branch/environment gate is part of the security boundary. Set the budget alert separately before deployment.

1. Create a dedicated S3 state bucket in the chosen region. Enable versioning, default encryption, and Block Public Access. Keep the bucket outside the app state so application teardown cannot delete its own state. Retain state after teardown for audit/recovery.
2. Configure the GitHub OIDC provider with URL `https://token.actions.githubusercontent.com` and audience `sts.amazonaws.com`; reuse an existing provider if the account already has it.
3. Create a dedicated deployment role. Its trust must allow `sts:AssumeRoleWithWebIdentity` only for that provider, with both exact string conditions:
   - `token.actions.githubusercontent.com:aud`: `sts.amazonaws.com`
   - `token.actions.githubusercontent.com:sub`: `repo:FrancoJim/portfolio-release-gate:environment:demo`
4. Attach a reviewed permissions policy. It needs lifecycle/read/tag operations for the named Lambda `hpl-release-gate`, log group `/aws/lambda/hpl-release-gate`, runtime IAM role `hpl-release-gate-runtime` and its inline log policy, and this demo's API Gateway v2 resources. Limit `iam:PassRole` to that runtime role with `iam:PassedToService = lambda.amazonaws.com`. Terraform also needs `s3:ListBucket` for the state prefix, Get/PutObject on `release-gate/demo.tfstate`, and Get/Put/DeleteObject on `release-gate/demo.tfstate.tflock`. Add KMS permissions if using a customer-managed state encryption key. Do not use AdministratorAccess as the deployment policy. API Gateway creation cannot be scoped to an API ID that does not exist yet; the account administrator must review that create permission and tighten scope after first deploy.
5. In GitHub create environment `demo`, restrict deployments to main, and set a required reviewer. Protect main and require CI. Set these environment variables: `AWS_REGION`, `AWS_ROLE_ARN`, `TF_STATE_BUCKET`. These are identifiers, not static access keys. Keep AWS credentials out of repository variables, files, and issue comments.

## Release

Run **Deploy demo** from main. The environment approval occurs before credentials are obtained. The job tests the application, assumes the role through OIDC, initializes encrypted and locked S3 state, validates, plans, applies the saved plan, and smoke-tests the result. This approval authorizes a run; it is not a second human review of the computed plan. For production, split plan/apply into separate jobs with review of the exact plan artifact.

The successful job summary provides the URL. Record the commit SHA, workflow run URL, service URL, and smoke-test result in the task. The first deploy remains unverified until that evidence exists.

## Recovery

For application regression: revert the offending commit through a reviewed change, wait for CI, and dispatch Deploy demo from main. Terraform updates the archive hash. This baseline deploys `$LATEST`; it does not implement Lambda alias canaries or instant alias rollback.

For failed apply: keep the state and lock evidence, inspect the error, and rerun only after fixing its cause. Never delete state to make a plan succeed. Only force-unlock after proving no other apply is active. If the cloud changed outside Terraform, review a fresh plan before proceeding.

## Teardown

Use an approved local AWS session for the same account and region. Initialize with the same backend settings used by the workflow, then review and apply a destroy plan:

```sh
terraform -chdir=infra init -backend-config="bucket=YOUR_STATE_BUCKET" -backend-config="key=release-gate/demo.tfstate" -backend-config="region=YOUR_REGION" -backend-config="encrypt=true" -backend-config="use_lockfile=true"
terraform -chdir=infra plan -destroy -var="region=YOUR_REGION" -out=destroy.tfplan
terraform -chdir=infra apply destroy.tfplan
```

The app log group is deleted with the app; export any evidence you need first. Confirm the endpoint no longer serves traffic. Retain the state bucket until recovery/audit needs end; the administrator separately removes the deployment role and any dedicated provider once no longer used. Never remove a shared OIDC provider.
