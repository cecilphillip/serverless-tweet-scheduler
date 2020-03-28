import logging
import json
import azure.functions as func
from azure.servicebus.aio import ServiceBusClient, Message
import os
import uuid
import datetime
from _datetime import timedelta


async def main(req: func.HttpRequest) -> func.HttpResponse:
    body_bytes = req.get_body()

    if not body_bytes:
        return func.HttpResponse(status_code=400)

    body_json = json.loads(body_bytes.decode())

    # Get queue client
    connection_str = os.environ['ServiceBusConnection']
    sb_client = ServiceBusClient.from_connection_string(connection_str)
    queue_client = sb_client.get_queue("scheduled-tweets")

    # Create Service Bus message
    status, time_delay = body_json.get(
        'statusUpdate'), body_json.get('minutesFromNow')
    message = Message(status)
    message.properties.message_id = uuid.uuid4()

    # schedule message
    enqueue_time = (datetime.utcnow() + timedelta(minutes=time_delay)
                    ).replace(microsecond=0)
    message.scheduled_enqueue_time
    message.schedule(enqueue_time)

    # Add message to queue
    await queue_client.send(message)

    return func.HttpResponse(status_code=201)
