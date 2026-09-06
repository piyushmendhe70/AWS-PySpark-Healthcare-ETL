variable "environment"    { type = string }
variable "project_name"   { type = string }
variable "s3_bucket_name" { type = string }
variable "s3_bucket_arn"  { type = string }

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../../../src/lambda/check_s3_file"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-${var.environment}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_s3_read" {
  name = "${var.project_name}-${var.environment}-lambda-s3"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket", "s3:HeadObject"]
      Resource = [var.s3_bucket_arn, "${var.s3_bucket_arn}/*"]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_read.arn
}

resource "aws_lambda_function" "check_s3_file" {
  function_name    = "${var.project_name}-${var.environment}-check-file"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30

  environment {
    variables = {
      LANDING_BUCKET = var.s3_bucket_name
    }
  }
}

output "lambda_arn"  { value = aws_lambda_function.check_s3_file.arn }
output "lambda_name" { value = aws_lambda_function.check_s3_file.function_name }