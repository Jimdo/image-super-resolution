output "region" {
  value = var.default_region
}

output "stage-bucket" {
  value = aws_s3_bucket.sharp_processed_images_bucket_stage.bucket
}

output "prod-bucket" {
  value = aws_s3_bucket.sharp_processed_images_bucket_prod.bucket
}

output "iam_role" {
  value = aws_iam_role.sharp_processed_images_bucket_iam_role.arn
}
