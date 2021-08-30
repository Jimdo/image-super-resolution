output "region" {
  value = var.default_region
}

output "bucket" {
  value = "s3://${aws_s3_bucket.sharp_processed_images_bucket.bucket}"
}

output "iam_role" {
  value = aws_iam_role.sharp_processed_images_bucket_iam_role.arn
}
