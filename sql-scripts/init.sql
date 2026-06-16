-- Cloud Cost Optimization Platform - Audit Schema
-- Tracks policy violations, approvals, and remediation results

CREATE TABLE IF NOT EXISTS dbo.Policies (
    PolicyId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    AzurePolicyId NVARCHAR(500) NOT NULL UNIQUE,
    PolicyName NVARCHAR(255) NOT NULL,
    PolicyDisplayName NVARCHAR(500),
    Scope NVARCHAR(500),
    DefinitionId NVARCHAR(500),
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 DEFAULT GETUTCDATE(),
    IsEnabled BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dbo.Violations (
    ViolationId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    PolicyId UNIQUEIDENTIFIER NOT NULL,
    SubscriptionId NVARCHAR(100) NOT NULL,
    ResourceGroupName NVARCHAR(255) NOT NULL,
    ResourceName NVARCHAR(500) NOT NULL,
    ResourceType NVARCHAR(255) NOT NULL,
    ResourceId NVARCHAR(1000) NOT NULL,
    OwnerEmail NVARCHAR(255),
    ComplianceState NVARCHAR(50), -- "NonCompliant", "Compliant", "Exempt", etc.
    EstimatedMonthlySavingsUSD DECIMAL(10, 2),
    RemediationType NVARCHAR(100), -- "DeleteResource", "ChangeConfig", "StopResource", etc.
    RecommendedAction NVARCHAR(1000),
    DetectedAt DATETIME2 NOT NULL,
    ExpiresAt DATETIME2, -- Approval window end
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 DEFAULT GETUTCDATE(),
    IsArchived BIT DEFAULT 0,
    FOREIGN KEY (PolicyId) REFERENCES dbo.Policies(PolicyId)
);

CREATE TABLE IF NOT EXISTS dbo.Approvals (
    ApprovalId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ViolationId UNIQUEIDENTIFIER NOT NULL,
    ApprovalWindowId NVARCHAR(100) NOT NULL,
    RequesterEmail NVARCHAR(255),
    ApproverEmail NVARCHAR(255),
    ApprovalStatus NVARCHAR(50), -- "Pending", "Approved", "Rejected", "Expired"
    ApprovedAt DATETIME2,
    RejectedAt DATETIME2,
    ApprovalReason NVARCHAR(1000),
    RejectionReason NVARCHAR(1000),
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (ViolationId) REFERENCES dbo.Violations(ViolationId)
);

CREATE TABLE IF NOT EXISTS dbo.RemediationExecutions (
    RemediationId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ApprovalId UNIQUEIDENTIFIER NOT NULL,
    ViolationId UNIQUEIDENTIFIER NOT NULL,
    GithubActionRunId NVARCHAR(100),
    RemediationStatus NVARCHAR(50), -- "Pending", "InProgress", "Succeeded", "Failed"
    TerraformOutput NVARCHAR(MAX),
    ErrorMessage NVARCHAR(MAX),
    EstimatedSavingsRealized DECIMAL(10, 2),
    TriggeredAt DATETIME2,
    CompletedAt DATETIME2,
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (ApprovalId) REFERENCES dbo.Approvals(ApprovalId),
    FOREIGN KEY (ViolationId) REFERENCES dbo.Violations(ViolationId)
);

CREATE TABLE IF NOT EXISTS dbo.AuditLog (
    AuditId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    EntityType NVARCHAR(100), -- "Policy", "Violation", "Approval", "Remediation"
    EntityId NVARCHAR(500),
    Action NVARCHAR(100), -- "Created", "Updated", "Approved", "Rejected", "Remediated"
    Actor NVARCHAR(255),
    OldValue NVARCHAR(MAX),
    NewValue NVARCHAR(MAX),
    Details NVARCHAR(MAX),
    CreatedAt DATETIME2 DEFAULT GETUTCDATE()
);

-- Indexes for common queries
CREATE INDEX idx_violations_policy ON dbo.Violations(PolicyId);
CREATE INDEX idx_violations_subscription ON dbo.Violations(SubscriptionId);
CREATE INDEX idx_violations_owner ON dbo.Violations(OwnerEmail);
CREATE INDEX idx_violations_detected ON dbo.Violations(DetectedAt);
CREATE INDEX idx_approvals_status ON dbo.Approvals(ApprovalStatus);
CREATE INDEX idx_approvals_window ON dbo.Approvals(ApprovalWindowId);
CREATE INDEX idx_remediation_status ON dbo.RemediationExecutions(RemediationStatus);
CREATE INDEX idx_audit_log_entity ON dbo.AuditLog(EntityType, EntityId);
