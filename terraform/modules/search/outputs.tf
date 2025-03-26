# Outputs from the search module

output "opensearch_endpoint" {
  description = "Endpoint for the OpenSearch domain"
  value       = aws_elasticsearch_domain.baller_search.endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "Dashboard endpoint for the OpenSearch domain"
  value       = aws_elasticsearch_domain.baller_search.kibana_endpoint
}

output "opensearch_domain_name" {
  description = "Name of the OpenSearch domain"
  value       = aws_elasticsearch_domain.baller_search.domain_name
}

output "opensearch_domain_id" {
  description = "ID of the OpenSearch domain"
  value       = aws_elasticsearch_domain.baller_search.domain_id
}

output "opensearch_arn" {
  description = "ARN of the OpenSearch domain"
  value       = aws_elasticsearch_domain.baller_search.arn
}

output "opensearch_version" {
  description = "Version of the OpenSearch/Elasticsearch engine"
  value       = aws_elasticsearch_domain.baller_search.elasticsearch_version
}
