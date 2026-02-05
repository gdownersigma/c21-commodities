provider "aws" {
  region = var.aws_region
}

resource "aws_security_group" "rds_sg" {
  name        = "c21-commodities-rds-sg"
  description = "Security group for PostgreSQL RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "c21-commodities-db-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "postgres" {
  identifier             = "c21-commodities-postgres"
  engine                 = "postgres"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  storage_type           = "gp3"
  storage_encrypted      = true
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  publicly_accessible    = true
  skip_final_snapshot    = true
}

resource "aws_ecr_repository" "pipeline" {
  name                 = "c21-commodities-pipeline"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_iam_role" "lambda_role" {
  name = "c21-commodities-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_ses" {
  name = "c21-commodities-lambda-ses-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ses:SendEmail",
        "ses:SendRawEmail",
        "ses:ListVerifiedEmailAddresses"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_lambda_function" "pipeline" {
  function_name = "c21-commodities-pipeline"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.pipeline.repository_url}:latest"
  timeout       = 600

  environment {
    variables = {
      DB_HOST     = aws_db_instance.postgres.address
      DB_PORT     = "5432"
      DB_NAME     = var.db_name
      DB_USER     = var.db_username
      DB_PASSWORD = var.db_password
      API_KEY     = var.api_key
    }
  }
}

resource "aws_iam_role" "sfn_role" {
  name = "c21-commodities-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "sfn_lambda" {
  name = "c21-commodities-sfn-lambda-policy"
  role = aws_iam_role.sfn_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "lambda:InvokeFunction"
      ]
      Resource = [
        aws_lambda_function.pipeline.arn,
        aws_lambda_function.price_alerts.arn
      ]
    }]
  })
}

resource "aws_sfn_state_machine" "pipeline_alerts" {
  name     = "c21-commodities-pipeline-alerts"
  role_arn = aws_iam_role.sfn_role.arn

  definition = jsonencode({
    Comment = "Pipeline to Price Alerts workflow"
    StartAt = "RunPipeline"
    States = {
      RunPipeline = {
        Type     = "Task"
        Resource = aws_lambda_function.pipeline.arn
        Next     = "RunPriceAlerts"
      }
      RunPriceAlerts = {
        Type     = "Task"
        Resource = aws_lambda_function.price_alerts.arn
        End      = true
      }
    }
  })
}

resource "aws_cloudwatch_event_rule" "pipeline_trigger" {
  name                = "c21-commodities-pipeline-trigger"
  schedule_expression = var.pipeline_schedule
}

resource "aws_cloudwatch_event_target" "sfn_target" {
  rule      = aws_cloudwatch_event_rule.pipeline_trigger.name
  target_id = "stepfunction"
  arn       = aws_sfn_state_machine.pipeline_alerts.arn
  role_arn  = aws_iam_role.eventbridge_sfn_role.arn
}

resource "aws_iam_role" "eventbridge_sfn_role" {
  name = "c21-commodities-eventbridge-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_sfn" {
  name = "c21-commodities-eventbridge-sfn-policy"
  role = aws_iam_role.eventbridge_sfn_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "states:StartExecution"
      Resource = aws_sfn_state_machine.pipeline_alerts.arn
    }]
  })
}

resource "aws_ecr_repository" "report" {
  name                 = "c21-commodities-report"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_lambda_function" "report" {
  function_name = "c21-commodities-report"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.report.repository_url}:latest"
  timeout       = 600
  memory_size   = 1024

  environment {
    variables = {
      DB_HOST      = aws_db_instance.postgres.address
      DB_PORT      = "5432"
      DB_NAME      = var.db_name
      DB_USER      = var.db_username
      DB_PASSWORD  = var.db_password
      MPLCONFIGDIR = "/tmp"
      SENDER_EMAIL = var.sender_email
    }
  }
}

resource "aws_cloudwatch_event_rule" "report_trigger" {
  name                = "c21-commodities-report-trigger"
  schedule_expression = var.report_schedule
}

resource "aws_cloudwatch_event_target" "report_target" {
  rule      = aws_cloudwatch_event_rule.report_trigger.name
  target_id = "lambda"
  arn       = aws_lambda_function.report.arn
}

resource "aws_lambda_permission" "report_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.report.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.report_trigger.arn
}

resource "aws_ecr_repository" "price_alerts" {
  name                 = "c21-commodities-price-alerts"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_lambda_function" "price_alerts" {
  function_name = "c21-commodities-price-alerts"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.price_alerts.repository_url}:latest"
  timeout       = 600
  memory_size   = 1024

  environment {
    variables = {
      DB_HOST      = aws_db_instance.postgres.address
      DB_PORT      = "5432"
      DB_NAME      = var.db_name
      DB_USER      = var.db_username
      DB_PASSWORD  = var.db_password
      SENDER_EMAIL = var.sender_email
    }
  }
}

resource "aws_ses_email_identity" "sender" {
  email = var.sender_email
}

resource "aws_ecr_repository" "historical_pipeline" {
  name                 = "c21-commodities-historical-pipeline"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_lambda_function" "historical_pipeline" {
  function_name = "c21-commodities-historical-pipeline"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.historical_pipeline.repository_url}:latest"
  timeout       = 600
  memory_size   = 1024

  environment {
    variables = {
      DB_HOST     = aws_db_instance.postgres.address
      DB_PORT     = "5432"
      DB_NAME     = var.db_name
      DB_USER     = var.db_username
      DB_PASSWORD = var.db_password
      API_KEY     = var.api_key
    }
  }
}