import pytest
import orders_pb2
import grpc
import os

from dotenv import load_dotenv
from google.protobuf.json_format import MessageToDict

from models import OrderModel

pytestmark = pytest.mark.asyncio
load_dotenv()

valid_token = os.environ.get('GRPC_AUTH_TOKEN')
valid_metadata = [("authorization", f"Bearer {valid_token}")]


async def test_get_order_details_success(order_stub):
    """
    Scenario:
        - requesting an existing order by its id using a valid token
    Expected result:
        - server returns correct order details (ID, status, item name, price, qty)
    """
    request = orders_pb2.OrderRequest(order_id="ORD-123")

    response = await order_stub.GetOrderDetails(request, metadata=valid_metadata)
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    validated_order = OrderModel(**response_dict)

    assert validated_order.id == "ORD-123"
    assert validated_order.status == "SHIPPED"
    assert validated_order.item_name == 'Coffee'
    assert validated_order.price == 29.99
    assert validated_order.quantity == 2


async def test_get_order_details_not_found(order_stub):
    """
    Scenario:
        - requesting an order by non existing ID using a valid token
    Expected result:
        - server returns NOT_FOUND error code
    """
    invalid_id = 'ORD-999'
    request = orders_pb2.OrderRequest(order_id=invalid_id)

    with pytest.raises(grpc.aio.AioRpcError) as exception_context:
        await order_stub.GetOrderDetails(request, metadata=valid_metadata)

    rpc_error = exception_context.value

    assert rpc_error.code() == grpc.StatusCode.NOT_FOUND
    error_details = rpc_error.details() or ""
    assert f"Order with ID '{invalid_id}' not found" in error_details


async def test_get_order_details_unauthenticated(order_stub):
    """
    Scenario:
        - requesting an order by valid ID using invalid token
    Expected result:
        - server returns UNAUTHENTICATED error code
    """
    request = orders_pb2.OrderRequest(order_id="ORD-123")
    # invalid token
    bad_metadata = [("authorization", "Bearer wrong-token")]

    with pytest.raises(grpc.aio.AioRpcError) as exception_context:
        await order_stub.GetOrderDetails(request, metadata=bad_metadata)

    rpc_error = exception_context.value
    assert rpc_error.code() == grpc.StatusCode.UNAUTHENTICATED
    assert "Missing or invalid authentication token" in (
        rpc_error.details() or "")
