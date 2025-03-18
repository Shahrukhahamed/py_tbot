class MessageFormatter:
    @staticmethod
    def format_notification(tx_data, received_token, rate):
        try:
            # Ensure amount and usd_value are properly formatted
            amount = float(tx_data['amount']) if 'amount' in tx_data else 0.0
            usd_value = float(tx_data['usd_value']) if 'usd_value' in tx_data else 0.0

            # Format the message string with rounded values
            return f"""
🔊🔊🔊 New Buy $ {received_token}
━━━━━━━━━━━━━━━━
💰 Spent: {amount:.4f} {tx_data['currency']} (${usd_value:.2f})
🎉 Got: {usd_value * rate:.2f} {received_token} (${usd_value * rate:.2f})
💱 Rate: {rate:.2f} $ {received_token}
🔗 Explorer: [View TX]({tx_data['explorer_url']})
            """
        except KeyError as e:
            # Log error if a key is missing from tx_data
            logger.log('error', f"Missing key in transaction data: {str(e)}")
            return "Error formatting notification."
        except Exception as e:
            # General error handling
            logger.log('error', f"Error formatting notification: {str(e)}")
            return "Error formatting notification."