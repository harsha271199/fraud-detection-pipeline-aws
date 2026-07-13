# Medallion architecture: bronze (raw), silver (cleaned/validated),
# gold (business-ready, feeds Redshift). One bucket, prefix-partitioned —
# simpler to manage than 3 buckets, and matches common real-world practice.

resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-datalake-${data.aws_caller_identity.current.account_id}"

  tags = { Name = "${var.project_name}-datalake" }
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket                  = aws_s3_bucket.data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle: raw bronze events are cheap to keep, but you don't need
# infinite retention on a demo project — expire after 30 days to keep the
# AWS bill near-zero. Adjust or remove once you're actively measuring.
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "expire-bronze"
    status = "Enabled"
    filter {
      prefix = "bronze/"
    }
    expiration {
      days = 30
    }
  }
}

output "data_lake_bucket_name" {
  value = aws_s3_bucket.data_lake.bucket
}
