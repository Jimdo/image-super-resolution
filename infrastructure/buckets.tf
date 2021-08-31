terraform {
  backend "s3" {
    bucket = "jimdo-sharp-processed-images-terraform-state-bucket"
    key    = "terraform.tfstate"
    region = "eu-west-1"
  }
}

resource "aws_s3_bucket" "sharp_processed_images_bucket_stage" {
  provider = aws
  bucket   = "${var.app_name}-stage"

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

resource "aws_s3_bucket" "sharp_processed_images_bucket_prod" {
  provider = aws
  bucket   = "${var.app_name}-prod"

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
