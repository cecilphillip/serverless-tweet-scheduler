import pulumi
from pulumi_azure import core, storage, servicebus, appservice, appinsights
from isodate import Duration, duration_isoformat

# Create an Azure Resource Group
resource_group = core.ResourceGroup('serverless-scheduler',
                                    name='serverless-scheduler',
                                    location='EastUs')

app_insights = appinsights.Insights('serverless-scheduler-ai',
                                    name='serverless-scheduler-ai',
                                    resource_group_name=resource_group.name,
                                    location=resource_group.location,
                                    application_type='web')

# Create an Azure Service Bus namespace
sbnamespace = servicebus.Namespace('serverless-scheduler-demo',
                                   sku='Standard',
                                   name='serverless-scheduler-demo',
                                   location='EastUs',
                                   resource_group_name=resource_group.name
                                   )

# Create an associated queue within the above namespace
servicebus.Queue('scheduled-tweets',
                 name='scheduled-tweets',
                 namespace_name=sbnamespace.name,
                 dead_lettering_on_message_expiration=True,
                 resource_group_name=resource_group.name,
                 max_size_in_megabytes=1024,
                 default_message_ttl=duration_isoformat(Duration(days=5))
                 )

# Create an Azure Storage Account
scheduler_account = storage.Account('serverlessschedulerstore',
                                    name='serverlessschedulerstore',
                                    account_kind="StorageV2",
                                    resource_group_name=resource_group.name,
                                    account_tier='Standard',
                                    account_replication_type='LRS')

scheduler_plan = appservice.Plan("serverless-scheduler",
                                 name='serverless-scheduler',
                                 resource_group_name=resource_group.name,
                                 kind="FunctionApp",
                                 reserved=True,
                                 sku={
                                      "tier": "Dynamic",
                                      "size": "Y1"
                                 })

scheduler_app = appservice.FunctionApp("serverless-scheduler",
                       name="serverless-scheduler",
                       resource_group_name=resource_group.name,
                       app_service_plan_id=scheduler_plan.id,
                       https_only=True,
                       os_type="linux",  # doesn't work??
                       storage_connection_string=scheduler_account.primary_connection_string,
                       version="~3",
                       app_settings={
                           "FUNCTIONS_WORKER_RUNTIME": "dotnet",
                           "APPINSIGHTS_INSTRUMENTATIONKEY": app_insights.instrumentation_key,
                           "ServiceBusConnection": sbnamespace.default_primary_connection_string,
                           "TwitterAPIKey": "",
                           "TwitterAPISecret": "",
                           "TwitterAccessToken": "",
                           "TwitterAccessTokenSecret": ""
                       })

# Export the connection string for the storage account
pulumi.export('storage account constr', scheduler_account.primary_connection_string)
pulumi.export('function app kind', scheduler_app.kind)
