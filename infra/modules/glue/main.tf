variable "environment"     { type = string }
variable "project_name"    { type = string }
variable "s3_bucket_name"  { type = string }
variable "s3_bucket_arn"   { type = string }

resource "aws_iam_role" "glue_role" {
  name = "${var.project_name}-${var.environment}-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_policy" "glue_s3_access" {
  name = "${var.project_name}-${var.environment}-glue-s3-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
      Resource = [var.s3_bucket_arn, "${var.s3_bucket_arn}/*"]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_s3_attach" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_s3_access.arn
}

resource "aws_glue_catalog_database" "ehs_catalog" {
  name = "${var.project_name}_${var.environment}_catalog"
}

resource "aws_glue_job" "ehs_etl_job" {
  name         = "${var.project_name}-${var.environment}-etl"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"
  worker_type  = "G.1X"
  number_of_workers = 5
  timeout      = 60

  command {
    name            = "glueetl"
    script_location = "s3://${var.s3_bucket_name}/scripts/main.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--continuous-log-logGroup"          = "/aws-glue/jobs/${var.project_name}-${var.environment}"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                   = "true"
  }
}

output "glue_job_name" { value = aws_glue_job.ehs_etl_job.name }
output "glue_job_arn"  { value = aws_glue_job.ehs_etl_job.arn }