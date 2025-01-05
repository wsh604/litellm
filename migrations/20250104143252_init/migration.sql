-- CreateTable
CREATE TABLE "LiteLLM_BudgetTable" (
    "budget_id" TEXT NOT NULL PRIMARY KEY,
    "max_budget" REAL,
    "soft_budget" REAL,
    "max_parallel_requests" INTEGER,
    "tpm_limit" BIGINT,
    "rpm_limit" BIGINT,
    "model_max_budget" TEXT NOT NULL DEFAULT '{}',
    "budget_duration" TEXT,
    "budget_reset_at" DATETIME,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" TEXT NOT NULL,
    "updated_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "LiteLLM_ProxyModelTable" (
    "model_id" TEXT NOT NULL PRIMARY KEY,
    "model_name" TEXT NOT NULL,
    "litellm_params" TEXT NOT NULL,
    "model_info" TEXT,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" TEXT NOT NULL,
    "updated_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "LiteLLM_OrganizationTable" (
    "organization_id" TEXT NOT NULL PRIMARY KEY,
    "organization_alias" TEXT NOT NULL,
    "budget_id" TEXT NOT NULL,
    "metadata" TEXT NOT NULL DEFAULT '{}',
    "models" TEXT NOT NULL,
    "spend" REAL NOT NULL DEFAULT 0.0,
    "model_spend" TEXT NOT NULL DEFAULT '{}',
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" TEXT NOT NULL,
    "updated_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" TEXT NOT NULL,
    CONSTRAINT "LiteLLM_OrganizationTable_budget_id_fkey" FOREIGN KEY ("budget_id") REFERENCES "LiteLLM_BudgetTable" ("budget_id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LiteLLM_ModelTable" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "model_aliases" TEXT,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" TEXT NOT NULL,
    "updated_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "LiteLLM_TeamTable" (
    "team_id" TEXT NOT NULL PRIMARY KEY,
    "team_alias" TEXT,
    "organization_id" TEXT,
    "admins" TEXT NOT NULL,
    "members" TEXT NOT NULL,
    "members_with_roles" TEXT NOT NULL DEFAULT '{}',
    "metadata" TEXT NOT NULL DEFAULT '{}',
    "max_budget" REAL,
    "spend" REAL NOT NULL DEFAULT 0.0,
    "models" TEXT NOT NULL,
    "max_parallel_requests" INTEGER,
    "tpm_limit" BIGINT,
    "rpm_limit" BIGINT,
    "budget_duration" TEXT,
    "budget_reset_at" DATETIME,
    "blocked" BOOLEAN NOT NULL DEFAULT false,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "model_spend" TEXT NOT NULL DEFAULT '{}',
    "model_max_budget" TEXT NOT NULL DEFAULT '{}',
    "model_id" INTEGER,
    CONSTRAINT "LiteLLM_TeamTable_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "LiteLLM_OrganizationTable" ("organization_id") ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "LiteLLM_TeamTable_model_id_fkey" FOREIGN KEY ("model_id") REFERENCES "LiteLLM_ModelTable" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LiteLLM_UserTable" (
    "user_id" TEXT NOT NULL PRIMARY KEY,
    "user_alias" TEXT,
    "team_id" TEXT,
    "organization_id" TEXT,
    "password" TEXT,
    "teams" TEXT NOT NULL DEFAULT '[]',
    "user_role" TEXT,
    "max_budget" REAL,
    "spend" REAL NOT NULL DEFAULT 0.0,
    "user_email" TEXT,
    "models" TEXT NOT NULL,
    "metadata" TEXT NOT NULL DEFAULT '{}',
    "max_parallel_requests" INTEGER,
    "tpm_limit" BIGINT,
    "rpm_limit" BIGINT,
    "budget_duration" TEXT,
    "budget_reset_at" DATETIME,
    "allowed_cache_controls" TEXT NOT NULL DEFAULT '[]',
    "model_spend" TEXT NOT NULL DEFAULT '{}',
    "model_max_budget" TEXT NOT NULL DEFAULT '{}',
    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "LiteLLM_UserTable_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "LiteLLM_OrganizationTable" ("organization_id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LiteLLM_VerificationToken" (
    "token" TEXT NOT NULL PRIMARY KEY,
    "key_name" TEXT,
    "key_alias" TEXT,
    "soft_budget_cooldown" BOOLEAN NOT NULL DEFAULT false,
    "spend" REAL NOT NULL DEFAULT 0.0,
    "expires" DATETIME,
    "models" TEXT NOT NULL,
    "aliases" TEXT NOT NULL DEFAULT '{}',
    "config" TEXT NOT NULL DEFAULT '{}',
    "user_id" TEXT,
    "team_id" TEXT,
    "permissions" TEXT NOT NULL DEFAULT '{}',
    "max_parallel_requests" INTEGER,
    "metadata" TEXT NOT NULL DEFAULT '{}',
    "blocked" BOOLEAN,
    "tpm_limit" BIGINT,
    "rpm_limit" BIGINT,
    "max_budget" REAL,
    "budget_duration" TEXT,
    "budget_reset_at" DATETIME,
    "allowed_cache_controls" TEXT NOT NULL DEFAULT '[]',
    "model_spend" TEXT NOT NULL DEFAULT '{}',
    "model_max_budget" TEXT NOT NULL DEFAULT '{}',
    "budget_id" TEXT,
    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "LiteLLM_VerificationToken_budget_id_fkey" FOREIGN KEY ("budget_id") REFERENCES "LiteLLM_BudgetTable" ("budget_id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LiteLLM_EndUserTable" (
    "user_id" TEXT NOT NULL PRIMARY KEY,
    "alias" TEXT,
    "spend" REAL NOT NULL DEFAULT 0.0,
    "allowed_model_region" TEXT,
    "default_model" TEXT,
    "budget_id" TEXT,
    "blocked" BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "LiteLLM_EndUserTable_budget_id_fkey" FOREIGN KEY ("budget_id") REFERENCES "LiteLLM_BudgetTable" ("budget_id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LiteLLM_Config" (
    "param_name" TEXT NOT NULL PRIMARY KEY,
    "param_value" TEXT
);

-- CreateTable
CREATE TABLE "LiteLLM_SpendLogs" (
    "request_id" TEXT NOT NULL PRIMARY KEY,
    "call_type" TEXT NOT NULL,
    "api_key" TEXT NOT NULL DEFAULT '',
    "spend" REAL NOT NULL DEFAULT 0.0,
    "total_tokens" INTEGER NOT NULL DEFAULT 0,
    "prompt_tokens" INTEGER NOT NULL DEFAULT 0,
    "completion_tokens" INTEGER NOT NULL DEFAULT 0,
    "startTime" DATETIME NOT NULL,
    "endTime" DATETIME NOT NULL,
    "completionStartTime" DATETIME,
    "model" TEXT NOT NULL DEFAULT '',
    "model_id" TEXT DEFAULT '',
    "model_group" TEXT DEFAULT '',
    "custom_llm_provider" TEXT DEFAULT '',
    "api_base" TEXT DEFAULT '',
    "user" TEXT DEFAULT '',
    "metadata" TEXT DEFAULT '{}',
    "cache_hit" TEXT DEFAULT '',
    "cache_key" TEXT DEFAULT '',
    "request_tags" TEXT DEFAULT '[]',
    "team_id" TEXT,
    "end_user" TEXT,
    "requester_ip_address" TEXT
);

-- CreateTable
CREATE TABLE "LiteLLM_ErrorLogs" (
    "request_id" TEXT NOT NULL PRIMARY KEY,
    "startTime" DATETIME NOT NULL,
    "endTime" DATETIME NOT NULL,
    "api_base" TEXT NOT NULL DEFAULT '',
    "model_group" TEXT NOT NULL DEFAULT '',
    "litellm_model_name" TEXT NOT NULL DEFAULT '',
    "model_id" TEXT NOT NULL DEFAULT '',
    "request_kwargs" TEXT NOT NULL DEFAULT '{}',
    "exception_type" TEXT NOT NULL DEFAULT '',
    "exception_string" TEXT NOT NULL DEFAULT '',
    "status_code" TEXT NOT NULL DEFAULT ''
);

-- CreateTable
CREATE TABLE "LiteLLM_UserNotifications" (
    "request_id" TEXT NOT NULL PRIMARY KEY,
    "user_id" TEXT NOT NULL,
    "models" TEXT NOT NULL,
    "justification" TEXT NOT NULL,
    "status" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "LiteLLM_TeamMembership" (
    "user_id" TEXT NOT NULL,
    "team_id" TEXT NOT NULL,
    "spend" REAL NOT NULL DEFAULT 0.0,
    "budget_id" TEXT,

    PRIMARY KEY ("user_id", "team_id"),
    CONSTRAINT "LiteLLM_TeamMembership_budget_id_fkey" FOREIGN KEY ("budget_id") REFERENCES "LiteLLM_BudgetTable" ("budget_id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LiteLLM_OrganizationMembership" (
    "user_id" TEXT NOT NULL,
    "organization_id" TEXT NOT NULL,
    "user_role" TEXT,
    "spend" REAL DEFAULT 0.0,
    "budget_id" TEXT,
    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY ("user_id", "organization_id"),
    CONSTRAINT "LiteLLM_OrganizationMembership_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "LiteLLM_UserTable" ("user_id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "LiteLLM_OrganizationMembership_budget_id_fkey" FOREIGN KEY ("budget_id") REFERENCES "LiteLLM_BudgetTable" ("budget_id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LiteLLM_InvitationLink" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "user_id" TEXT NOT NULL,
    "is_accepted" BOOLEAN NOT NULL DEFAULT false,
    "accepted_at" DATETIME,
    "expires_at" DATETIME NOT NULL,
    "created_at" DATETIME NOT NULL,
    "created_by" TEXT NOT NULL,
    "updated_at" DATETIME NOT NULL,
    "updated_by" TEXT NOT NULL,
    CONSTRAINT "LiteLLM_InvitationLink_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "LiteLLM_UserTable" ("user_id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "LiteLLM_InvitationLink_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "LiteLLM_UserTable" ("user_id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "LiteLLM_InvitationLink_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "LiteLLM_UserTable" ("user_id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LiteLLM_AuditLog" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "updated_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "changed_by" TEXT NOT NULL DEFAULT '',
    "changed_by_api_key" TEXT NOT NULL DEFAULT '',
    "action" TEXT NOT NULL,
    "table_name" TEXT NOT NULL,
    "object_id" TEXT NOT NULL,
    "before_value" TEXT,
    "updated_values" TEXT
);

-- CreateTable
CREATE TABLE "assistants" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "assistantId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "instructions" TEXT,
    "metadata_text" TEXT,
    "tools_text" TEXT NOT NULL,
    "model" TEXT NOT NULL,
    "fileIds_text" TEXT NOT NULL,
    "avatarPath" TEXT,
    "avatarSource" TEXT,
    "conversationStarters_text" TEXT NOT NULL,
    "appendCurrentDatetime" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "assistants_userId_fkey" FOREIGN KEY ("userId") REFERENCES "wuban_user_mapping" ("wuban_user_id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "agents" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "instructions" TEXT,
    "context" TEXT,
    "avatar" TEXT,
    "modelParameters_text" TEXT,
    "tools_text" TEXT NOT NULL,
    "isCollaborative" BOOLEAN NOT NULL DEFAULT false,
    "projectIds_text" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "agents_userId_fkey" FOREIGN KEY ("userId") REFERENCES "wuban_user_mapping" ("wuban_user_id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "conversation" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "conversationId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "title" TEXT,
    "model" TEXT,
    "modelDisplayLabel" TEXT,
    "endpoint" TEXT,
    "endpointType" TEXT,
    "isArchived" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "conversation_userId_fkey" FOREIGN KEY ("userId") REFERENCES "wuban_user_mapping" ("wuban_user_id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "message" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "messageId" TEXT NOT NULL,
    "conversationId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "text" TEXT NOT NULL,
    "sender" TEXT NOT NULL,
    "parentMessageId" TEXT,
    "isCreatedByUser" BOOLEAN NOT NULL DEFAULT false,
    "model" TEXT,
    "endpoint" TEXT,
    "endpointType" TEXT,
    "error" TEXT,
    "unfinished" BOOLEAN NOT NULL DEFAULT false,
    "isEdited" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "message_conversationId_fkey" FOREIGN KEY ("conversationId") REFERENCES "conversation" ("conversationId") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "message_userId_fkey" FOREIGN KEY ("userId") REFERENCES "wuban_user_mapping" ("wuban_user_id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "file" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "fileId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "size" INTEGER NOT NULL,
    "url" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "file_userId_fkey" FOREIGN KEY ("userId") REFERENCES "wuban_user_mapping" ("wuban_user_id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "message_file" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "messageId" TEXT NOT NULL,
    "fileId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "message_file_messageId_fkey" FOREIGN KEY ("messageId") REFERENCES "message" ("messageId") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "message_file_fileId_fkey" FOREIGN KEY ("fileId") REFERENCES "file" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "conversation_tag" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "conversationId" TEXT NOT NULL,
    "tag" TEXT NOT NULL,
    "color" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "conversation_tag_conversationId_fkey" FOREIGN KEY ("conversationId") REFERENCES "conversation" ("conversationId") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "wuban_user_mapping" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "wuban_user_id" TEXT NOT NULL,
    "litellm_user_id" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "LiteLLM_TeamTable_model_id_key" ON "LiteLLM_TeamTable"("model_id");

-- CreateIndex
CREATE INDEX "LiteLLM_SpendLogs_startTime_idx" ON "LiteLLM_SpendLogs"("startTime");

-- CreateIndex
CREATE INDEX "LiteLLM_SpendLogs_end_user_idx" ON "LiteLLM_SpendLogs"("end_user");

-- CreateIndex
CREATE UNIQUE INDEX "LiteLLM_OrganizationMembership_user_id_organization_id_key" ON "LiteLLM_OrganizationMembership"("user_id", "organization_id");

-- CreateIndex
CREATE UNIQUE INDEX "assistants_assistantId_key" ON "assistants"("assistantId");

-- CreateIndex
CREATE UNIQUE INDEX "conversation_conversationId_key" ON "conversation"("conversationId");

-- CreateIndex
CREATE UNIQUE INDEX "message_messageId_key" ON "message"("messageId");

-- CreateIndex
CREATE UNIQUE INDEX "file_fileId_key" ON "file"("fileId");

-- CreateIndex
CREATE UNIQUE INDEX "message_file_messageId_fileId_key" ON "message_file"("messageId", "fileId");

-- CreateIndex
CREATE UNIQUE INDEX "conversation_tag_conversationId_tag_key" ON "conversation_tag"("conversationId", "tag");

-- CreateIndex
CREATE UNIQUE INDEX "wuban_user_mapping_wuban_user_id_key" ON "wuban_user_mapping"("wuban_user_id");
