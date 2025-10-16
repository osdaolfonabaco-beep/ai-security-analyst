# --- Configuración del Proveedor ---
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# --- Recurso del Bucket S3 ---
resource "aws_s3_bucket" "log_bucket" {
  bucket = "david-proyecto5-unique-name-12345"
}

# --- IAM Role para la Función Lambda ---
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda-security-analyzer-ia-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# --- Política del Rol (CON EL PERMISO CORREGIDO PARA BEDROCK) ---
resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda-security-analyzer-ia-policy"
  role = aws_iam_role.lambda_exec_role.id
  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:us-east-1:*:*"
      },
      {
        Action   = "s3:GetObject",
        Effect   = "Allow",
        Resource = "${aws_s3_bucket.log_bucket.arn}/*"
      },
      {
        # --- INICIO: Permiso CORREGIDO para Amazon Bedrock ---
        Action   = "bedrock:InvokeModel",
        Effect   = "Allow",
        # La corrección está en esta línea. Usamos "foundation-model"
        Resource = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        # --- FIN: Permiso CORREGIDO para Amazon Bedrock ---
      }
    ]
  })
}

# --- Recurso para el archivo .zip que subiremos a S3 ---
resource "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.log_bucket.id
  key    = "function.zip"
  source = "../lambda_function.zip"
  etag   = filemd5("../lambda_function.zip")
}

# --- Recurso de la Función Lambda ---
resource "aws_lambda_function" "security_analyzer_lambda" {
  s3_bucket        = aws_s3_bucket.log_bucket.id
  s3_key           = aws_s3_object.lambda_zip.key
  source_code_hash = aws_s3_object.lambda_zip.etag

  function_name = "SecurityLogAnalyzerIA"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "main.handler"
  runtime       = "python3.9"
  timeout       = 60

  depends_on = [aws_s3_object.lambda_zip]
}

# --- Permiso para que S3 pueda invocar la Lambda ---
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3ToInvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.security_analyzer_lambda.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.log_bucket.arn
}

# --- Notificación de evento en S3 (El Disparador) ---
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.log_bucket.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.security_analyzer_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".log"
  }
  depends_on = [aws_lambda_permission.allow_s3]
}
