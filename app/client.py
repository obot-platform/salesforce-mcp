import os
from simple_salesforce import Salesforce
from fastmcp.exceptions import ToolError


def get_salesforce_client() -> Salesforce:
    """Create and return a Salesforce client using environment variables."""
    consumer_key = os.environ.get('SFDC_CLIENT_ID')
    consumer_secret = os.environ.get('SFDC_CLIENT_SECRET')
    domain = os.environ.get('SFDC_DOMAIN', 'organization.my')
    
    if not consumer_key:
        raise ToolError("SFDC_CLIENT_ID environment variable is required")
    if not consumer_secret:
        raise ToolError("SFDC_CLIENT_SECRET environment variable is required")
    
    return Salesforce(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        domain=domain
    )