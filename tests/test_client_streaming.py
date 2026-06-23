import pytest
import orders_pb2
import asyncio
import os

from dotenv import load_dotenv


pytestmark = pytest.mark.asyncio
load_dotenv()

valid_token = os.environ.get('GRPC_AUTH_TOKEN')
valid_metadata = [("authorization", f"Bearer {valid_token}")]


async def order_payload_generator():
    items = ["Keyboard", "HDMI Cable", "Desk Mat"]

    for idx, item in enumerate(items, start=1):
        yield orders_pb2.OrderResponse(
            id=f"BULK-{idx}",
            item_name=item,
            price=15.00 * idx,
            quantity=1,
            status="PENDING"
        )
    await asyncio.sleep(0.5)


async def test_bulk_create_orders_client_stream(order_stub):
    """
    Scenario:
        - uploading multiple orders at once
    Expected result:
        - the server returns a single msg confirming that all orders have been imported
    """
    summary_response = await order_stub.BulkCreateOrders(order_payload_generator(),
                                                         metadata=valid_metadata)

    assert summary_response.total_processed == 3
    assert summary_response.success is True
    assert "Successfully imported 3 orders" in summary_response.message
