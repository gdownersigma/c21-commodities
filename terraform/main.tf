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

resource "aws_ecr_repository" "dashboard" {
  name                 = "c21-commodities-dashboard"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

data "aws_ecs_cluster" "main" {
  cluster_name = var.ecs_cluster_name
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "c21-commodities-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_cloudwatch_log_group" "dashboard" {
  name              = "/ecs/c21-commodities-dashboard"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "dashboard" {
  family                   = "c21-commodities-dashboard"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([{
    name      = "dashboard"
    image     = "${aws_ecr_repository.dashboard.repository_url}:latest"
    essential = true
    portMappings = [{
      containerPort = 8501
      hostPort      = 8501
      protocol      = "tcp"
    }]
    environment = [
      { name = "DB_HOST", value = aws_db_instance.postgres.address },
      { name = "DB_PORT", value = "5432" },
      { name = "DB_NAME", value = var.db_name },
      { name = "DB_USER", value = var.db_username },
      { name = "DB_PASSWORD", value = var.db_password }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.dashboard.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_security_group" "dashboard_alb" {
  name        = "c21-commodities-dashboard-alb-sg"
  description = "Security group for Dashboard ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "dashboard_ecs" {
  name        = "c21-commodities-dashboard-ecs-sg"
  description = "Security group for Dashboard ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.dashboard_alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "dashboard" {
  name               = "c21-commodities-dashboard-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.dashboard_alb.id]
  subnets            = var.subnet_ids
}

resource "aws_lb_target_group" "dashboard" {
  name        = "c21-commodities-dashboard-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/_stcore/health"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 60
    interval            = 120
    matcher             = "200"
  }
}

resource "aws_lb_listener" "dashboard" {
  load_balancer_arn = aws_lb.dashboard.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.dashboard.arn
  }
}

resource "aws_ecs_service" "dashboard" {
  name            = "c21-commodities-dashboard-service"
  cluster         = data.aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.dashboard.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.dashboard_ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.dashboard.arn
    container_name   = "dashboard"
    container_port   = 8501
  }

  depends_on = [aws_lb_listener.dashboard]
}

output "dashboard_url" {
  value       = "http://${aws_lb.dashboard.dns_name}"
  description = "Dashboard URL"
}