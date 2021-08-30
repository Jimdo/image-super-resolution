resource "aws_s3_bucket" "sharp_processed_images_bucket" {
  provider = aws
  bucket   = "${var.app_name}-${terraform.workspace}"

  acl = "private"

  lifecycle {
      ignore_changes = [
        replication_configuration
      ]
  }

  lifecycle_rule {
    enabled = true

    expiration {
      expired_object_delete_marker = true
    }

    noncurrent_version_expiration {
      days = 30
    }
  }

  tags = {
    "jimdo:cost-group" = "sharp"
  }
}

resource "aws_iam_policy" "sharp_processed_images_bucket_policy" {
  name = "${var.app_name}-${terraform.workspace}-bucket-policy"
  description = "Policy with full access to the ${aws_s3_bucket.sharp_processed_images_bucket.bucket} bucket."
  policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
      {
        Effect: "Allow",
        Action: "s3:*",
        Resource:["${aws_s3_bucket.sharp_processed_images_bucket.arn}/*"],
      }
    ]
  })
}

resource "aws_iam_role" "sharp_processed_images_bucket_iam_role" {
  name = "${var.app_name}-${terraform.workspace}-bucket-iam-role"

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_policy_attachment" "sharp_processed_images_bucket_policy_attachment" {
  name = "${var.app_name}-${terraform.workspace}-bucket-policy-attachment"
  roles = ["${aws_iam_role.sharp_processed_images_bucket_iam_role.name}"]
  policy_arn = "${aws_iam_policy.sharp_processed_images_bucket_policy.arn}"
}
