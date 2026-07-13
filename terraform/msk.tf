# Amazon MSK — managed Kafka. Smallest viable broker size for a portfolio
# project; bump msk_broker_instance_type in variables.tf if you need more
# throughput to hit a specific events/sec target for your README numbers.

resource "aws_security_group" "msk" {
  name_prefix = "${var.project_name}-msk-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Kafka broker access - restricted to your IP only (see my_ip_cidr)"
    from_port   = 9092
    to_port     = 9198
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-msk-sg" }
}

resource "aws_msk_configuration" "main" {
  name           = "fraud-pipeline-config"
  kafka_versions = [var.msk_kafka_version]
  server_properties = <<PROPERTIES
allow.everyone.if.no.acl.found=false
auto.create.topics.enable=true
default.replication.factor=2
min.insync.replicas=1
num.partitions=3
PROPERTIES
}

resource "aws_msk_cluster" "main" {
configuration_info {
    arn      = aws_msk_configuration.main.arn
    revision = aws_msk_configuration.main.latest_revision
  }
  cluster_name           = "${var.project_name}-cluster"
  kafka_version           = var.msk_kafka_version
  number_of_broker_nodes = 2

  # NOTE: MSK public access (connectivity_info.public_access below) is a
  # newer feature and its exact requirements (e.g. TLS-only client_broker
  # encryption) can shift between provider versions. If `terraform plan`
  # errors on this block, check the aws_msk_cluster docs for your
  # installed AWS provider version — the fix is usually a one-line
  # encryption_info adjustment, not a redesign.
  broker_node_group_info {
    instance_type   = var.msk_broker_instance_type
    client_subnets  = aws_subnet.public[*].id
    security_groups = [aws_security_group.msk.id]

    connectivity_info {
     public_access {
        type = "SERVICE_PROVIDED_EIPS"
      }
    }

    storage_info {
      ebs_storage_info {
        volume_size = 20
      }
    }
  }

  client_authentication {
    unauthenticated = false
    sasl {
      scram = true
      iam   = true
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  tags = { Name = "${var.project_name}-msk" }
}

output "msk_bootstrap_brokers_tls" {
  description = "TLS bootstrap broker string - use this in producer/consumer configs"
  value       = aws_msk_cluster.main.bootstrap_brokers_tls
}

output "msk_bootstrap_brokers_sasl_scram" {
  description = "PRIVATE SASL/SCRAM bootstrap brokers - only reachable from within the VPC, not from your laptop"
  value       = aws_msk_cluster.main.bootstrap_brokers_sasl_scram
}

output "msk_bootstrap_brokers_public_sasl_scram" {
  description = "PUBLIC SASL/SCRAM bootstrap brokers - USE THIS ONE for producer/consumer/kafka-acls running from your local machine"
  value       = aws_msk_cluster.main.bootstrap_brokers_public_sasl_scram
}

resource "aws_kms_key" "msk_scram" {
  description             = "KMS key for MSK SASL/SCRAM secret encryption"
  deletion_window_in_days = 7
}

resource "aws_secretsmanager_secret" "msk_scram" {
  name       = "AmazonMSK_fraud-pipeline_scram"
  kms_key_id = aws_kms_key.msk_scram.arn
}

resource "aws_secretsmanager_secret_version" "msk_scram" {
  secret_id = aws_secretsmanager_secret.msk_scram.id
  secret_string = jsonencode({
    username = "fraudpipeline"
    password = var.msk_scram_password
  })
}

resource "aws_msk_scram_secret_association" "main" {
  cluster_arn     = aws_msk_cluster.main.arn
  secret_arn_list = [aws_secretsmanager_secret.msk_scram.arn]

  depends_on = [aws_secretsmanager_secret_version.msk_scram]
}
