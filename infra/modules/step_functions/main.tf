variable "environment"                { type = string }
variable "project_name"               { type = string }
variable "check_s3_file_lambda_arn"   { type = string }
variable "glue_job_name"              { type = string }
variable "s3_data_bucket"             { type = string }
variable "sns_alert_topic_arn"        { type = string }

resource "aws_iam_role" "sfn_role" {
  name = "${var.project_name}-${var.environment}-sfn-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "sfn_policy" {
  name = "${var.project_name}-${var.environment}-sfn-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = ["${var.check_s3_file_lambda_arn}*"]
      },
      {
        Effect   = "Allow"
        Action   = ["glue:StartJobRun", "glue:GetJobRun", "glue:GetJobRuns", "glue:BatchStopJobRun"]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = [var.sns_alert_topic_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sfn_attach" {
  role       = aws_iam_role.sfn_role.name
  policy_arn = aws_iam_policy.sfn_policy.arn
}

resource "aws_sfn_state_machine" "etl_pipeline" {
  name     = "${var.project_name}-${var.environment}-pipeline"
  role_arn = aws_iam_role.sfn_role.arn

  definition = templatefile("${path.root}/../../../stepfunctions/etl_pipeline.asl.json", {
    check_s3_file_lambda_arn = var.check_s3_file_lambda_arn
    glue_job_name            = var.glue_job_name
    s3_data_bucket           = var.s3_data_bucket
    environment              = var.environment
    sns_alert_topic_arn      = var.sns_alert_topic_arn
  })
}

output "state_machine_arn" { value = aws_sfn_state_machine.etl_pipeline.arn }