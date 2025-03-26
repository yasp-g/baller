# Outputs from the search module

output "opensearch_endpoint" {
  description = "Endpoint for the OpenSearch domain"
  value       = aws_elasticsearch_domain.baller_search.endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "Dashboard endpoint for the OpenSearch domain"
  value       = aws_elasticsearch_domain.baller_search.kibana_endpoint
}
