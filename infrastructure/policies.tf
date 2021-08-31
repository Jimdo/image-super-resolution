resource "aws_iam_policy" "sharp_processed_images_bucket_policy" {
  name = "${var.app_name}-bucket-policy"
  description = "Policy with full access to the stage and prod ${var.app_name} buckets."
  policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
      {
        Effect: "Allow",
        Action: "s3:*",
        Resource:[
          "${aws_s3_bucket.sharp_processed_images_bucket_stage.arn}/*",
          "${aws_s3_bucket.sharp_processed_images_bucket_prod.arn}/*"
        ],
      }
    ]
  })
}

resource "aws_iam_role" "sharp_processed_images_bucket_iam_role" {
  name = "${var.app_name}-bucket-iam-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          # Taken from https://github.com/Jimdo/sre-wonderland-mirror-roles/issues/35
          AWS = "arn:aws:iam::691344588897:role/wonderland-mirror-role-sharp-image-super-resolution-jimdo"
        }
      },
    ]
  })
}

resource "aws_iam_policy_attachment" "sharp_processed_images_bucket_policy_attachment" {
  name = "${var.app_name}-bucket-policy-attachment"
  roles = ["${aws_iam_role.sharp_processed_images_bucket_iam_role.name}"]
  policy_arn = "${aws_iam_policy.sharp_processed_images_bucket_policy.arn}"
}

resource "local_file" "aws_config_file" {
  filename = "${path.module}/aws_config.txt"
  content = <<-EOT
    [profile ecs]
    role_arn = ${aws_iam_role.sharp_processed_images_bucket_iam_role.arn}
    credential_source = EcsContainer
  EOT
}
