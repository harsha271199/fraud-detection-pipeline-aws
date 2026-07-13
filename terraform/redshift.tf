# Redshift SERVERLESS — not a provisioned cluster. Bills per-second only
# while a query is actively running, and drops to $0 compute cost when
# idle. New AWS accounts get a $300 free trial credit (90 days) that
# likely covers this project's entire Redshift usage. This replaces the
# ~$180/month provisioned dc2.large cluster from the original design.

resource "aws_security_group" "redshift" {
  name_prefix = "${var.project_name}-redshift-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Redshift access - restricted to your IP only (see my_ip_cidr)"
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-redshift-sg" }
}

resource "aws_redshiftserverless_namespace" "main" {
  namespace_name      = "${var.project_name}-namespace"
  db_name              = "frauddb"
  admin_username       = var.redshift_master_username
  admin_user_password = var.redshift_master_password
  iam_roles            = [aws_iam_role.redshift_s3_read.arn]
  default_iam_role_arn = aws_iam_role.redshift_s3_read.arn

  tags = { Name = "${var.project_name}-redshift-namespace" }
}

resource "aws_redshiftserverless_workgroup" "main" {
  namespace_name     = aws_redshiftserverless_namespace.main.namespace_name
  workgroup_name     = "${var.project_name}-workgroup"
  base_capacity      = var.redshift_base_rpu
  subnet_ids         = aws_subnet.public[*].id
  security_group_ids = [aws_security_group.redshift.id]

  # publicly_accessible = true because we're on public subnets with no
  # NAT/private-subnet setup in this cost-minimized version. Security
  # comes from the SG being locked to your IP (my_ip_cidr), not network
  # isolation. Fine for a demo; would be private-subnet-only in prod.
  publicly_accessible = true

  tags = { Name = "${var.project_name}-redshift-workgroup" }
}

output "redshift_serverless_endpoint" {
  value = aws_redshiftserverless_workgroup.main.endpoint
}
