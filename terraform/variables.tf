variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Short project identifier used in resource names"
  type        = string
  default     = "fraud-pipeline"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "my_ip_cidr" {
  description = "Your home/dev IP in CIDR form (e.g. 1.2.3.4/32) — restricts MSK and Redshift Serverless access to just you, since there's no NAT/private subnet in this cost-minimized setup. Find your IP at whatismyip.com. Do NOT leave this as 0.0.0.0/0 for anything longer than a short dev session."
  type        = string
}

variable "redshift_master_username" {
  description = "Master username for the Redshift Serverless namespace"
  type        = string
  default     = "fraudadmin"
}

variable "redshift_master_password" {
  description = "Master password for Redshift Serverless — set via TF_VAR_redshift_master_password env var, never commit"
  type        = string
  sensitive   = true
}

variable "redshift_base_rpu" {
  description = "Redshift Serverless base capacity in RPUs. 8 is the minimum in us-east-1; some regions allow 4. Only billed while queries are actively running."
  type        = number
  default     = 8
}

variable "msk_kafka_version" {
  description = "Kafka version for the MSK cluster"
  type        = string
  default     = "3.6.0"
}

variable "msk_broker_instance_type" {
  description = "MSK broker instance type — smallest viable for a demo workload"
  type        = string
  default     = "kafka.t3.small"
}

variable "msk_scram_password" {
  type      = string
  sensitive = true
}
