variable "environment" { type = string }
variable "project_name" { type = string }

resource "aws_s3_bucket" "data_lake" {
  bucket        = "${var.project_name}-${var.environment}-lake"
  force_destroy = false

  tags = {
    Environment = var.environment
    Project     = var.project_name
    DataLayer   = "Medallion-Lake"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake_encryption" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lake_public_block" {
  bucket                  = aws_s3_bucket.data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_name" { value = aws_s3_bucket.data_lake.id }
output "bucket_arn" { value = aws_s3_bucket.data_lake.arn }