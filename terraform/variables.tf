# Variables for the root Terraform module

# Environment
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

# AWS region
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

# Project name
variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "baller"
}
