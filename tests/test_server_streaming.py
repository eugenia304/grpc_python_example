import pytest
import os

import orders_pb2

from dotenv import load_dotenv
from google.protobuf.json_format import MessageToDict

from models import OrderModel

pytestmark = pytest.mark.asyncio
load_dotenv()

valid_token = os.environ.get('GRPC_AUTH_TOKEN')
valid_metadata = [("authorization", f"Bearer {valid_token}")]


async def test_track_order_lifecycle_stream(order_stub):
    """
    Scenario:
        - tracking the order status updates in real-time
    Expected result:
        - the server streams back the status updates (pending -> shipped -> delivered)
    """
    request = orders_pb2.OrderRequest(order_id='ORD-789')
    captured_statuses = []

    response_stream = order_stub.TrackOrder(
        request, metadata=valid_metadata)

    # Looping through the stream
    async for response in response_stream:
        response_dict = MessageToDict(
            response, preserving_proto_field_name=True)

        # Validating structure
        validated_update = OrderModel(**response_dict)

        # Tracking statuses sequence
        captured_statuses.append(validated_update.status)

    assert len(captured_statuses) == 3
    assert captured_statuses == ["PENDING", "SHIPPED", "DELIVERED"]
