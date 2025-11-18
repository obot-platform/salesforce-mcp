import json
from typing import Annotated, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from .client import get_salesforce_client

mcp = FastMCP(
    name="SalesforceMCP",
    on_duplicate_tools="error",
    on_duplicate_resources="warn",
    on_duplicate_prompts="replace",
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "healthy"})


@mcp.tool(name="describe_contact_schema")
async def describe_contact_schema() -> dict:
    """Describes the available fields for a contact object in Salesforce."""
    try:
        sf = get_salesforce_client()
        schema = sf.Contact.describe()
        fields = []
        for field in schema['fields']:
            fields.append({
                'name': field['name'],
                'label': field['label'],
                'type': field['type'],
                'required': field['nillable'] == False,
                'createable': field['createable'],
                'updateable': field['updateable'],
                'picklistValues': field.get('picklistValues', [])
            })
        return {"schema": {"object": "Contact", "fields": fields}}
    except Exception as e:
        raise ToolError(f"Failed to describe contact schema: {e}")


@mcp.tool(name="create_contact")
async def create_contact(
    contact: Annotated[
        str, Field(description="A JSON-formatted string containing the contact fields to use for the new contact")
    ]
) -> dict:
    """Create a new contact in Salesforce."""
    try:
        sf = get_salesforce_client()
        contact_data = json.loads(contact)
        result = sf.Contact.create(contact_data)
        return {"message": f"Contact created successfully with Id: {result['id']}", "id": result['id']}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for contact data")
    except Exception as e:
        raise ToolError(f"Failed to create contact: {e}")


@mcp.tool(name="update_contact")
async def update_contact(
    contact: Annotated[
        str, Field(description="A JSON-formatted string containing the contact fields to update in the existing contact")
    ],
    contact_id: Annotated[str, Field(description="A string containing the Salesforce Id of the contact to update")]
) -> dict:
    """Update an existing contact in Salesforce."""
    try:
        sf = get_salesforce_client()
        contact_data = json.loads(contact)
        result = sf.Contact.update(contact_id, contact_data)
        return {"message": f"Contact {contact_id} updated successfully"}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for contact data")
    except Exception as e:
        raise ToolError(f"Failed to update contact: {e}")


@mcp.tool(name="delete_contact")
async def delete_contact(
    contact_id: Annotated[str, Field(description="A string containing the Salesforce Id of the contact to delete")]
) -> dict:
    """Delete an existing contact in Salesforce."""
    try:
        sf = get_salesforce_client()
        result = sf.Contact.delete(contact_id)
        return {"message": f"Contact {contact_id} deleted successfully"}
    except Exception as e:
        raise ToolError(f"Failed to delete contact: {e}")


@mcp.tool(name="describe_lead_schema")
async def describe_lead_schema() -> dict:
    """Describes the available fields for a lead object in Salesforce."""
    try:
        sf = get_salesforce_client()
        schema = sf.Lead.describe()
        fields = []
        for field in schema['fields']:
            fields.append({
                'name': field['name'],
                'label': field['label'],
                'type': field['type'],
                'required': field['nillable'] == False,
                'createable': field['createable'],
                'updateable': field['updateable'],
                'picklistValues': field.get('picklistValues', [])
            })
        return {"schema": {"object": "Lead", "fields": fields}}
    except Exception as e:
        raise ToolError(f"Failed to describe lead schema: {e}")


@mcp.tool(name="create_lead")
async def create_lead(
    lead: Annotated[
        str, Field(description="A JSON-formatted string containing the lead fields to use for the new lead")
    ]
) -> dict:
    """Create a new lead in Salesforce."""
    try:
        sf = get_salesforce_client()
        lead_data = json.loads(lead)
        result = sf.Lead.create(lead_data)
        return {"message": f"Lead created successfully with Id: {result['id']}", "id": result['id']}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for lead data")
    except Exception as e:
        raise ToolError(f"Failed to create lead: {e}")


@mcp.tool(name="update_lead")
async def update_lead(
    lead: Annotated[
        str, Field(description="A JSON-formatted string containing the lead fields to update in the existing lead")
    ],
    lead_id: Annotated[str, Field(description="A string containing the Salesforce Id of the lead to update")]
) -> dict:
    """Update an existing lead in Salesforce."""
    try:
        sf = get_salesforce_client()
        lead_data = json.loads(lead)
        result = sf.Lead.update(lead_id, lead_data)
        return {"message": f"Lead {lead_id} updated successfully"}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for lead data")
    except Exception as e:
        raise ToolError(f"Failed to update lead: {e}")


@mcp.tool(name="delete_lead")
async def delete_lead(
    lead_id: Annotated[str, Field(description="A string containing the Salesforce Id of the lead to delete")]
) -> dict:
    """Delete an existing lead in Salesforce."""
    try:
        sf = get_salesforce_client()
        result = sf.Lead.delete(lead_id)
        return {"message": f"Lead {lead_id} deleted successfully"}
    except Exception as e:
        raise ToolError(f"Failed to delete lead: {e}")


@mcp.tool(name="convert_lead_to_opportunity")
async def convert_lead_to_opportunity(
    lead_id: Annotated[str, Field(description="A string containing the Salesforce Id of the lead to update")],
    converted_status: Annotated[str, Field(description="The converted status of the lead. Must exist within Salesforce.")],
    opportunity_name: Annotated[str, Field(description="The name of the opportunity to create")],
    account_id: Annotated[Optional[str], Field(description="The Salesforce Id of an existing account to associate with the opportunity")] = None,
    contact_id: Annotated[Optional[str], Field(description="The Salesforce Id of an existing contact to associate with the opportunity")] = None,
) -> dict:
    """Converts an existing lead into a new Opportunity in Salesforce."""
    try:
        sf = get_salesforce_client()
        
        convert_data = {
            'leadId': lead_id,
            'convertedStatus': converted_status,
            'opportunityName': opportunity_name
        }
        
        if account_id:
            convert_data['accountId'] = account_id
        if contact_id:
            convert_data['contactId'] = contact_id
            
        result = sf.apexecute('apex/ConvertLead', method='POST', data=convert_data)
        return {"message": f"Lead {lead_id} converted successfully to opportunity: {opportunity_name}"}
    except Exception as e:
        raise ToolError(f"Failed to convert lead to opportunity: {e}")


@mcp.tool(name="describe_account_schema")
async def describe_account_schema() -> dict:
    """Describes the available fields for an account object in Salesforce."""
    try:
        sf = get_salesforce_client()
        schema = sf.Account.describe()
        fields = []
        for field in schema['fields']:
            fields.append({
                'name': field['name'],
                'label': field['label'],
                'type': field['type'],
                'required': field['nillable'] == False,
                'createable': field['createable'],
                'updateable': field['updateable'],
                'picklistValues': field.get('picklistValues', [])
            })
        return {"schema": {"object": "Account", "fields": fields}}
    except Exception as e:
        raise ToolError(f"Failed to describe account schema: {e}")


@mcp.tool(name="create_account")
async def create_account(
    account: Annotated[
        str, Field(description="A JSON-formatted string containing the account fields to use for the new account")
    ]
) -> dict:
    """Create a new account in Salesforce."""
    try:
        sf = get_salesforce_client()
        account_data = json.loads(account)
        result = sf.Account.create(account_data)
        return {"message": f"Account created successfully with Id: {result['id']}", "id": result['id']}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for account data")
    except Exception as e:
        raise ToolError(f"Failed to create account: {e}")


@mcp.tool(name="update_account")
async def update_account(
    account: Annotated[
        str, Field(description="A JSON-formatted string containing the account fields to update in the existing account")
    ],
    account_id: Annotated[str, Field(description="A string containing the Salesforce Id of the account to update")]
) -> dict:
    """Update an existing account in Salesforce."""
    try:
        sf = get_salesforce_client()
        account_data = json.loads(account)
        result = sf.Account.update(account_id, account_data)
        return {"message": f"Account {account_id} updated successfully"}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for account data")
    except Exception as e:
        raise ToolError(f"Failed to update account: {e}")


@mcp.tool(name="delete_account")
async def delete_account(
    account_id: Annotated[str, Field(description="A string containing the Salesforce Id of the account to delete")]
) -> dict:
    """Delete an existing account in Salesforce."""
    try:
        sf = get_salesforce_client()
        result = sf.Account.delete(account_id)
        return {"message": f"Account {account_id} deleted successfully"}
    except Exception as e:
        raise ToolError(f"Failed to delete account: {e}")


@mcp.tool(name="describe_opportunity_schema")
async def describe_opportunity_schema() -> dict:
    """Describes the available fields for an opportunity object in Salesforce."""
    try:
        sf = get_salesforce_client()
        schema = sf.Opportunity.describe()
        fields = []
        for field in schema['fields']:
            fields.append({
                'name': field['name'],
                'label': field['label'],
                'type': field['type'],
                'required': field['nillable'] == False,
                'createable': field['createable'],
                'updateable': field['updateable'],
                'picklistValues': field.get('picklistValues', [])
            })
        return {"schema": {"object": "Opportunity", "fields": fields}}
    except Exception as e:
        raise ToolError(f"Failed to describe opportunity schema: {e}")


@mcp.tool(name="create_opportunity")
async def create_opportunity(
    opportunity: Annotated[
        str, Field(description="A JSON-formatted string containing the opportunity fields to use for the new opportunity")
    ]
) -> dict:
    """Create a new opportunity in Salesforce."""
    try:
        sf = get_salesforce_client()
        opportunity_data = json.loads(opportunity)
        result = sf.Opportunity.create(opportunity_data)
        return {"message": f"Opportunity created successfully with Id: {result['id']}", "id": result['id']}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for opportunity data")
    except Exception as e:
        raise ToolError(f"Failed to create opportunity: {e}")


@mcp.tool(name="update_opportunity")
async def update_opportunity(
    opportunity: Annotated[
        str, Field(description="A JSON-formatted string containing the opportunity fields to update in the existing opportunity")
    ],
    opportunity_id: Annotated[str, Field(description="A string containing the Salesforce Id of the opportunity to update")]
) -> dict:
    """Update an existing opportunity in Salesforce."""
    try:
        sf = get_salesforce_client()
        opportunity_data = json.loads(opportunity)
        result = sf.Opportunity.update(opportunity_id, opportunity_data)
        return {"message": f"Opportunity {opportunity_id} updated successfully"}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for opportunity data")
    except Exception as e:
        raise ToolError(f"Failed to update opportunity: {e}")


@mcp.tool(name="delete_opportunity")
async def delete_opportunity(
    opportunity_id: Annotated[str, Field(description="A string containing the Salesforce Id of the opportunity to delete")]
) -> dict:
    """Delete an existing opportunity in Salesforce."""
    try:
        sf = get_salesforce_client()
        result = sf.Opportunity.delete(opportunity_id)
        return {"message": f"Opportunity {opportunity_id} deleted successfully"}
    except Exception as e:
        raise ToolError(f"Failed to delete opportunity: {e}")


@mcp.tool(name="describe_case_schema")
async def describe_case_schema() -> dict:
    """Describes the available fields for a case object in Salesforce."""
    try:
        sf = get_salesforce_client()
        schema = sf.Case.describe()
        fields = []
        for field in schema['fields']:
            fields.append({
                'name': field['name'],
                'label': field['label'],
                'type': field['type'],
                'required': field['nillable'] == False,
                'createable': field['createable'],
                'updateable': field['updateable'],
                'picklistValues': field.get('picklistValues', [])
            })
        return {"schema": {"object": "Case", "fields": fields}}
    except Exception as e:
        raise ToolError(f"Failed to describe case schema: {e}")


@mcp.tool(name="create_case")
async def create_case(
    case: Annotated[
        str, Field(description="A JSON-formatted string containing the case fields to use for the new case")
    ]
) -> dict:
    """Create a new case in Salesforce."""
    try:
        sf = get_salesforce_client()
        case_data = json.loads(case)
        result = sf.Case.create(case_data)
        return {"message": f"Case created successfully with Id: {result['id']}", "id": result['id']}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for case data")
    except Exception as e:
        raise ToolError(f"Failed to create case: {e}")


@mcp.tool(name="update_case")
async def update_case(
    case: Annotated[
        str, Field(description="A JSON-formatted string containing the case fields to update in the existing case")
    ],
    case_id: Annotated[str, Field(description="A string containing the Salesforce Id of the case to update")]
) -> dict:
    """Update an existing case in Salesforce."""
    try:
        sf = get_salesforce_client()
        case_data = json.loads(case)
        result = sf.Case.update(case_id, case_data)
        return {"message": f"Case {case_id} updated successfully"}
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON provided for case data")
    except Exception as e:
        raise ToolError(f"Failed to update case: {e}")


@mcp.tool(name="delete_case")
async def delete_case(
    case_id: Annotated[str, Field(description="A string containing the Salesforce Id of the case to delete")]
) -> dict:
    """Delete an existing case in Salesforce."""
    try:
        sf = get_salesforce_client()
        result = sf.Case.delete(case_id)
        return {"message": f"Case {case_id} deleted successfully"}
    except Exception as e:
        raise ToolError(f"Failed to delete case: {e}")


@mcp.tool(name="query")
async def query(
    query: Annotated[str, Field(description="The SOQL query to execute")]
) -> dict:
    """Query Salesforce using SOQL."""
    try:
        sf = get_salesforce_client()
        result = sf.query(query)
        
        records = []
        for record in result['records']:
            records.append(record)
            
        response = {
            "totalSize": result['totalSize'],
            "done": result['done'],
            "records": records
        }
        
        # Handle pagination
        if not result['done'] and 'nextRecordsUrl' in result:
            response['nextRecordsUrl'] = result['nextRecordsUrl']
            
        return response
    except Exception as e:
        raise ToolError(f"Failed to execute query: {e}")


@mcp.tool(name="get_direct_link")
async def get_direct_link(
    object_type: Annotated[str, Field(description="The type of Salesforce object to get the direct link for. Use singular form, starting with a capital letter (e.g., Account, Contact, Lead, Opportunity, Case)")],
    object_id: Annotated[str, Field(description="The ID of the Salesforce object to get the direct link for.")]
) -> dict:
    """Get a direct weblink to a Salesforce object."""
    try:
        sf = get_salesforce_client()
        # Extract the base URL from the instance URL
        instance_url = sf.sf_instance
        if not instance_url.startswith('https://'):
            instance_url = f"https://{instance_url}"
        
        direct_url = f"{instance_url}/{object_id}"
        return {"url": direct_url, "object_type": object_type, "object_id": object_id}
    except Exception as e:
        raise ToolError(f"Failed to get direct link: {e}")


@mcp.tool(name="email_message")
async def email_message(
    related_object_id: Annotated[str, Field(description="The Salesforce Id of the object to which the email should be related")],
    subject: Annotated[str, Field(description="The subject of the email")],
    text_body: Annotated[str, Field(description="The plaintext body of the email")],
    html_body: Annotated[str, Field(description="The HTML body of the email")],
    from_name: Annotated[str, Field(description="The name of the sender")],
    from_address: Annotated[str, Field(description="The email address of the sender")],
    to_address: Annotated[str, Field(description="The email address of the recipient")],
    status: Annotated[int, Field(description="The numeric status of the email (3 = Sent, 5 = Draft). Create messages as drafts by default.")] = 5,
) -> dict:
    """Create an Email in Salesforce using Enhanced Email functionality."""
    try:
        sf = get_salesforce_client()
        
        email_data = {
            'RelatedToId': related_object_id,
            'Subject': subject,
            'TextBody': text_body,
            'HtmlBody': html_body,
            'FromName': from_name,
            'FromAddress': from_address,
            'ToAddress': to_address,
            'Status': status
        }
        
        result = sf.EmailMessage.create(email_data)
        status_text = "Draft" if status == 5 else "Sent" if status == 3 else "Unknown"
        return {"message": f"Email message created successfully with Id: {result['id']} (Status: {status_text})", "id": result['id']}
    except Exception as e:
        raise ToolError(f"Failed to create email message: {e}")


def streamable_http_server():
    """Main entry point for the Salesforce MCP server."""
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=9000,
        path="/",
    )


if __name__ == "__main__":
    streamable_http_server()