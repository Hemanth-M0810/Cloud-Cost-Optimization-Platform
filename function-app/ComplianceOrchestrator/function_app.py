"""
Cloud Cost Optimization Platform - Compliance Orchestrator Function App
Queries Azure Policy Insights API to detect non-compliant resources and stores results in Azure SQL.
"""

import azure.functions as func
import json
import os
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from azure.identity import DefaultAzureCredential
from azure.mgmt.policyinsights import PolicyInsightsClient
from azure.mgmt.subscription import SubscriptionClient
from azure.data.tables import TableServiceClient
import pyodbc

# Configuration
SUBSCRIPTION_IDS = os.getenv("SUBSCRIPTION_IDS", "").split(",")
SQL_CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING", "")
APPROVAL_WINDOW_DAYS = int(os.getenv("APPROVAL_WINDOW_DAYS", "7"))
POLICY_IDS = os.getenv("POLICY_IDS", "").split(",")  # Azure Policy Definition IDs to scan

logger = logging.getLogger("ComplianceOrchestrator")

app = func.FunctionApp()


def get_sql_connection():
    """Create and return Azure SQL database connection."""
    if not SQL_CONNECTION_STRING:
        raise ValueError("SQL_CONNECTION_STRING not configured")
    return pyodbc.connect(SQL_CONNECTION_STRING)


def query_policy_insights(subscription_id: str) -> list[dict]:
    """
    Query Azure Policy Insights API for non-compliant resources.
    
    Args:
        subscription_id: Azure subscription to scan
        
    Returns:
        List of non-compliant resources with details
    """
    credential = DefaultAzureCredential()
    client = PolicyInsightsClient(credential=credential)
    
    non_compliant_resources = []
    
    try:
        # Query policy states to find non-compliant resources
        query_results = client.policy_states.list_query_results_for_subscription(
            subscription_id=subscription_id,
            filter="IsCompliant eq false",
            top=1000
        )
        
        for result in query_results.value:
            non_compliant_resources.append({
                "policyDefinitionId": result.policy_definition_id,
                "policySetDefinitionId": result.policy_set_definition_id,
                "resourceId": result.resource_id,
                "complianceState": result.compliance_state,
                "subscriptionId": subscription_id,
                "timestamp": result.timestamp,
            })
            
    except Exception as e:
        logger.error(f"Error querying Policy Insights for subscription {subscription_id}: {str(e)}")
    
    return non_compliant_resources


def extract_resource_details(resource_id: str) -> dict:
    """Extract resource group and resource name from ARM resource ID."""
    parts = resource_id.lower().split("/")
    try:
        rg_index = parts.index("resourcegroups")
        resource_group = parts[rg_index + 1]
        resource_name = parts[-1]
        return {"resourceGroup": resource_group, "resourceName": resource_name}
    except (ValueError, IndexError):
        return {"resourceGroup": "unknown", "resourceName": "unknown"}


def store_violations_in_sql(violations: list[dict], policy_id: str) -> int:
    """
    Store detected violations in Azure SQL database.
    
    Args:
        violations: List of non-compliant resources
        policy_id: Policy identifier
        
    Returns:
        Count of stored violations
    """
    if not violations:
        return 0
    
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()
        
        stored_count = 0
        window_end = (datetime.utcnow() + timedelta(days=APPROVAL_WINDOW_DAYS)).isoformat()
        
        for violation in violations:
            resource_details = extract_resource_details(violation["resourceId"])
            violation_id = str(uuid4())
            
            try:
                cursor.execute("""
                    INSERT INTO dbo.Violations (
                        ViolationId, PolicyId, SubscriptionId, ResourceGroupName, 
                        ResourceName, ResourceType, ResourceId, ComplianceState, 
                        EstimatedMonthlySavingsUSD, RemediationType, DetectedAt, ExpiresAt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    violation_id,
                    policy_id,
                    violation["subscriptionId"],
                    resource_details["resourceGroup"],
                    resource_details["resourceName"],
                    "Unknown",  # Would need to query Azure for full resource type
                    violation["resourceId"],
                    violation["complianceState"],
                    0.0,  # Estimated savings (would be policy-specific)
                    "Review",
                    violation.get("timestamp", datetime.utcnow()),
                    window_end
                ))
                stored_count += 1
            except Exception as e:
                logger.warning(f"Failed to insert violation {violation['resourceId']}: {str(e)}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return stored_count
    except Exception as e:
        logger.error(f"Database error storing violations: {str(e)}")
        return 0


@app.timer_trigger(arg_name="myTimer", schedule="0 0 * * * *")  # Daily at midnight UTC
def ComplianceOrchestrator(myTimer: func.TimerRequest) -> None:
    """
    Main orchestrator function.
    1. Queries Azure Policy Insights for non-compliant resources
    2. Stores violations in Azure SQL
    3. Triggers Logic App for approval workflow (via HTTP webhook)
    """
    
    logger.info(f"Compliance Orchestrator triggered at {datetime.utcnow()}")
    
    if not SUBSCRIPTION_IDS or SUBSCRIPTION_IDS == ['']:
        logger.error("SUBSCRIPTION_IDS not configured")
        return
    
    total_violations = 0
    
    for subscription_id in SUBSCRIPTION_IDS:
        subscription_id = subscription_id.strip()
        if not subscription_id:
            continue
            
        logger.info(f"Scanning subscription {subscription_id}")
        
        # Query Policy Insights
        violations = query_policy_insights(subscription_id)
        
        if violations:
            logger.info(f"Found {len(violations)} non-compliant resources in {subscription_id}")
            
            # Store in SQL
            policy_id = os.getenv("DEFAULT_POLICY_ID", str(uuid4()))
            stored = store_violations_in_sql(violations, policy_id)
            total_violations += stored
            
            # TODO: Trigger Logic App for approval workflow
            # Call Logic App HTTP endpoint to notify approvers
    
    logger.info(f"Compliance scan complete. Found {total_violations} violations.")


@app.function_name("GetViolations")
@app.route(route="violations", methods=["GET"])
def get_violations(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint to retrieve recent violations.
    Query params: days_back (int), status (str)
    """
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()
        
        days_back = req.params.get("days_back", "7")
        status = req.params.get("status", "")
        
        query = "SELECT * FROM dbo.Violations WHERE DetectedAt >= DATEADD(day, ?, GETUTCDATE())"
        params = [int(days_back) * -1]
        
        if status:
            query += " AND ComplianceState = ?"
            params.append(status)
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        violations = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return func.HttpResponse(
            json.dumps([{k: str(v) if isinstance(v, (datetime, type(None))) else v for k, v in v.items()} for v in violations]),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Error retrieving violations: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)


@app.function_name("GetApprovals")
@app.route(route="approvals", methods=["GET"])
def get_approvals(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint to retrieve pending approvals.
    Query params: status (str)
    """
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()
        
        status = req.params.get("status", "Pending")
        
        cursor.execute("SELECT * FROM dbo.Approvals WHERE ApprovalStatus = ?", (status,))
        columns = [desc[0] for desc in cursor.description]
        approvals = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return func.HttpResponse(
            json.dumps([{k: str(v) if isinstance(v, (datetime, type(None))) else v for k, v in v.items()} for v in approvals]),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Error retrieving approvals: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
