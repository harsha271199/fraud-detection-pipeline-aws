terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment once you've created a state bucket (do this manually, once,
  # before first `terraform init` — chicken-and-egg problem otherwise):
  # backend "s3" {
  #   bucket = "fraud-pipeline-tfstate-<your-unique-suffix>"
  #   key    = "fraud-pipeline/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "fraud-pipeline"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}
