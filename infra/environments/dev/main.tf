terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# SNS Notifications Topic
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"
}

module "s3" {
  source       = "../../modules/s3"
  environment  = var.environment
  project_name = var.project_name
}

module "glue" {
  source         = "../../modules/glue"
  environment    = var.environment
  project_name   = var.project_name
  s3_bucket_name = module.s3.bucket_name
  s3_bucket_arn  = module.s3.bucket_arn
}

module "lambda" {
  source         = "../../modules/lambda"
  environment    = var.environment
  project_name   = var.project_name
  s3_bucket_name = module.s3.bucket_name
  s3_bucket_arn  = module.s3.bucket_arn
}

module "step_functions" {
  source                   = "../../modules/step_functions"
  environment              = var.environment
  project_name             = var.project_name
  check_s3_file_lambda_arn = module.lambda.lambda_arn
  glue_job_name            = module.glue.glue_job_name
  s3_data_bucket           = module.s3.bucket_name
  sns_alert_topic_arn      = aws_sns_topic.alerts.arn
}