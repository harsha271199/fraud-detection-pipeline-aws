# Least-privilege IAM: a single role for the consumer/producer app (EC2 or
# ECS task) that can read/write the data lake and publish CloudWatch metrics,
# and a separate role for Redshift to read from S3 (COPY command).

resource "aws_iam_role" "pipeline_app" {
  name = "${var.project_name}-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "pipeline_app_s3" {
  name = "${var.project_name}-app-s3-access"
  role = aws_iam_role.pipeline_app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
      Resource = [
        aws_s3_bucket.data_lake.arn,
        "${aws_s3_bucket.data_lake.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "pipeline_app_cloudwatch" {
  name = "${var.project_name}-app-cloudwatch"
  role = aws_iam_role.pipeline_app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["cloudwatch:PutMetricData"]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role" "redshift_s3_read" {
  name = "${var.project_name}-redshift-s3-read"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "redshift.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "redshift_s3_read_policy" {
  name = "${var.project_name}-redshift-s3-read-policy"
  role = aws_iam_role.redshift_s3_read.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [aws_s3_bucket.data_lake.arn, "${aws_s3_bucket.data_lake.arn}/*"]
    }]
  })
}

resource "aws_iam_role_policy" "redshift_glue_catalog" {
  name = "fraud-pipeline-redshift-glue-catalog"
  role = aws_iam_role.redshift_s3_read.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "glue:CreateDatabase",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:CreateTable",
        "glue:GetTable",
        "glue:GetTables",
        "glue:UpdateTable",
        "glue:DeleteTable",
        "glue:GetPartitions",
        "glue:GetPartition",
        "glue:BatchCreatePartition"
      ]
      Resource = "*"
    }]
  })
}

output "redshift_s3_read_role_arn" {
  value = aws_iam_role.redshift_s3_read.arn
}
