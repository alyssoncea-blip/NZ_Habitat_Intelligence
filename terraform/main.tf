# ECR Repository
resource "aws_ecr_repository" "nz_habitat" {
  name                 = "${var.app_name}-dashboard"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.app_name}-ecr"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "nz_habitat" {
  name = "${var.app_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.app_name}-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "nz_habitat" {
  family                   = "${var.app_name}-dashboard"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "dashboard"
      image     = var.container_image
      essential = true
      portMappings = [
        {
          containerPort = 8050
          hostPort      = 8050
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.nz_habitat.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "dashboard"
        }
      }
      environment = [
        {
          name  = "PYTHONUNBUFFERED"
          value = "1"
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        },
        {
          name  = "DATA_BUCKET"
          value = aws_s3_bucket.nz_habitat_data.id
        }
      ]
      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8050')\" || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
    },
    {
      name      = "prefect-server"
      image     = "prefecthq/prefect:2-python3.11"
      essential = false
      portMappings = [
        {
          containerPort = 4200
          hostPort      = 4200
          protocol      = "tcp"
        }
      ]
      command = ["prefect", "server", "start", "--host", "0.0.0.0"]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.nz_habitat.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "prefect"
        }
      }
    }
  ])

  tags = {
    Name = "${var.app_name}-task"
  }
}

# ECS Service
resource "aws_ecs_service" "nz_habitat_dashboard" {
  name            = "${var.app_name}-dashboard-service"
  cluster         = aws_ecs_cluster.nz_habitat.id
  task_definition = aws_ecs_task_definition.nz_habitat.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.nz_habitat_dashboard.arn
    container_name   = "dashboard"
    container_port   = 8050
  }

  tags = {
    Name = "${var.app_name}-service"
  }
}

# Application Load Balancer
resource "aws_lb" "nz_habitat" {
  name               = "${var.app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "${var.app_name}-alb"
  }
}

resource "aws_lb_target_group" "nz_habitat_dashboard" {
  name        = "${var.app_name}-dashboard-tg"
  port        = 8050
  protocol    = "HTTP"
  vpc_id      = aws_vpc.nz_habitat.id
  target_type = "ip"

  health_check {
    path                = "/"
    port                = "8050"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
  }
}

resource "aws_lb_listener" "nz_habitat" {
  load_balancer_arn = aws_lb.nz_habitat.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.nz_habitat_dashboard.arn
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "nz_habitat" {
  name              = "/ecs/${var.app_name}"
  retention_in_days = 30

  tags = {
    Name = "${var.app_name}-logs"
  }
}

# S3 Bucket for Data
resource "aws_s3_bucket" "nz_habitat_data" {
  bucket = "${var.app_name}-data-${var.aws_region}"

  tags = {
    Name = "${var.app_name}-data"
  }
}

resource "aws_s3_bucket_versioning" "nz_habitat_data" {
  bucket = aws_s3_bucket.nz_habitat_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "nz_habitat_data" {
  bucket = aws_s3_bucket.nz_habitat_data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# IAM Roles
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.app_name}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name = "${var.app_name}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "${var.app_name}-ecs-task-s3"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.nz_habitat_data.arn,
          "${aws_s3_bucket.nz_habitat_data.arn}/*",
        ]
      }
    ]
  })
}
