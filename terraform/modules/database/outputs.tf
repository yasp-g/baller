# Outputs from the database module

output "conversations_table_name" {
  description = "Name of the conversations table"
  value       = aws_dynamodb_table.conversations.name
}

output "messages_table_name" {
  description = "Name of the messages table"
  value       = aws_dynamodb_table.messages.name
}

output "preferences_table_name" {
  description = "Name of the preferences table"
  value       = aws_dynamodb_table.preferences.name
}
