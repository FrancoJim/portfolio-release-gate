# Administrator-only bootstrap. Keep this state private and backed up.
terraform {
  required_version = "~> 1.12.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
provider "aws" {
  region = var.region
}
variable "region" {
  type    = string
  default = "us-east-1"
}
variable "state_bucket_name" {
  type = string
}
variable "existing_oidc_provider_arn" {
  type        = string
  default     = null
  description = "Supply the existing GitHub OIDC provider ARN if one already exists in this account."
}
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
locals {
  prefix  = "arn:${data.aws_partition.current.partition}"
  account = data.aws_caller_identity.current.account_id
  runtime = "${local.prefix}:iam::${local.account}:role/hpl-release-gate-runtime"
}
resource "aws_s3_bucket" "state" {
  bucket = var.state_bucket_name
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Sid       = "DenyInsecureTransport", Effect = "Deny", Principal = "*", Action = "s3:*",
    Resource  = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"],
    Condition = { Bool = { "aws:SecureTransport" = "false" } }
  }] })
}
resource "aws_iam_openid_connect_provider" "github" {
  count          = var.existing_oidc_provider_arn == null ? 1 : 0
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}
resource "aws_iam_role" "deploy" {
  name = "hpl-release-gate-deploy"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect    = "Allow", Action = "sts:AssumeRoleWithWebIdentity",
    Principal = { Federated = var.existing_oidc_provider_arn != null ? var.existing_oidc_provider_arn : aws_iam_openid_connect_provider.github[0].arn },
    Condition = { StringEquals = {
      "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub" = "repo:FrancoJim/portfolio-release-gate:environment:demo"
    } }
  }] })
}
resource "aws_iam_role_policy" "deploy" {
  role = aws_iam_role.deploy.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["lambda:*"], Resource = "${local.prefix}:lambda:${var.region}:${local.account}:function:hpl-release-gate" },
    { Effect = "Allow", Action = ["logs:CreateLogGroup", "logs:DeleteLogGroup", "logs:PutRetentionPolicy", "logs:DeleteRetentionPolicy", "logs:TagResource", "logs:UntagResource", "logs:ListTagsForResource"], Resource = "${local.prefix}:logs:${var.region}:${local.account}:log-group:/aws/lambda/hpl-release-gate*" },
    { Effect = "Allow", Action = ["logs:DescribeLogGroups"], Resource = "*" },
    { Effect = "Allow", Action = ["iam:CreateRole", "iam:DeleteRole", "iam:GetRole", "iam:UpdateRole", "iam:UpdateRoleDescription", "iam:UpdateAssumeRolePolicy", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies", "iam:PutRolePolicy", "iam:GetRolePolicy", "iam:DeleteRolePolicy", "iam:TagRole", "iam:UntagRole"], Resource = local.runtime },
    { Effect = "Allow", Action = "iam:PassRole", Resource = local.runtime, Condition = { StringEquals = { "iam:PassedToService" = "lambda.amazonaws.com" } } },
    # API IDs do not exist until creation. Use a dedicated demo account;
    # narrow this management scope to the created API after first deployment.
    { Effect = "Allow", Action = ["apigateway:GET", "apigateway:POST", "apigateway:PATCH", "apigateway:DELETE", "apigateway:PUT"], Resource = ["${local.prefix}:apigateway:${var.region}::/apis", "${local.prefix}:apigateway:${var.region}::/apis/*", "${local.prefix}:apigateway:${var.region}::/tags/*"] },
    { Effect = "Allow", Action = "s3:ListBucket", Resource = aws_s3_bucket.state.arn },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject"], Resource = "${aws_s3_bucket.state.arn}/release-gate/demo.tfstate" },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = "${aws_s3_bucket.state.arn}/release-gate/demo.tfstate.tflock" }
  ] })
}
output "github_variables" {
  value = { AWS_REGION = var.region, AWS_ROLE_ARN = aws_iam_role.deploy.arn, TF_STATE_BUCKET = aws_s3_bucket.state.id }
}
