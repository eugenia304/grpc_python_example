import pytest
import orders_pb2
import asyncio
import os

from dotenv import load_dotenv

pytestmark = pytest.mark.asyncio

load_dotenv()

valid_token = os.environ.get('GRPC_AUTH_TOKEN')
valid_metadata = [("authorization", f"Bearer {valid_token}")]


async def user_chat_generator():
    # msg examples
    queries = [
        ("ORD-101", "Where is my package?"),
        ("ORD-102", "I want to cancel this order."),
        ("ORD-103", "The item arrived damaged.")
    ]

    for order_id, text in queries:
        yield orders_pb2.ChatMessage(
            order_id=order_id,
            message_text=text,
        )
    await asyncio.sleep(0.5)


async def test_order_support_bidirectional_stream(order_stub):
    """
    Scenario:
        - 3 incoming msgs being sent
    Expected result:
        - the server replies to each message with the predefined response
            containing order id
    """
    response_stream = order_stub.OrderSupportChat(user_chat_generator(),
                                                  metadata=valid_metadata)
    captured_replies = []

    # Read server responses
    async for response in response_stream:
        captured_replies.append(response)
        print(
            f"[Client Test] Received chat response for order: {response.order_id}")

    assert len(captured_replies) == 3
    assert captured_replies[0].order_id == 'ORD-101'
    assert captured_replies[1].order_id == 'ORD-102'
    assert captured_replies[2].order_id == 'ORD-103'
    assert "looking into your query" in captured_replies[0].reply_text
