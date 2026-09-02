import datetime

class TextChannelAdapter:
    def send(self, intervention: dict, contact: dict, payment_link_url: str = None, payment_link_id: str = None) -> dict:
        """
        Simulated send for WhatsApp / SMS / Email.
        Returns a DeliveryResult dictionary.
        """
        message = f"Hello. You have an outstanding payment. "
        if payment_link_url:
            message += f"Please pay here: {payment_link_url}"
            
        # Simulate expected failures
        if contact.get("opted_out"):
            return {
                "channel": "text",
                "status": "failed",
                "response_payload": {"error": "User opted out of text communications"}
            }
            
        # Always return delivered for text channel (no auto-fake responses)
        response_payload = {"message_sent": message, "simulated": True}
        if payment_link_url:
            response_payload["short_url"] = payment_link_url
        if payment_link_id:
            response_payload["link_id"] = payment_link_id

        return {
            "channel": "text",
            "status": "delivered",
            "response_payload": response_payload
        }
