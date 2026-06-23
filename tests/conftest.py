import pytest
import grpc
import os

import orders_pb2_grpc

from dotenv import load_dotenv

from mock_server import MockOrderService
from interceptors import AsyncAuthInterceptor

load_dotenv()


@pytest.fixture(scope="function", autouse=True)
async def start_mock_server():
    """
    Starts the mock server in the background for each test
    """
    secret_token = os.environ.get("GRPC_AUTH_TOKEN", '')
    port = os.environ.get('GRPC_SERVER_PORT')

    auth_interceptor = AsyncAuthInterceptor(secret_token=secret_token)
    server = grpc.aio.server(interceptors=[auth_interceptor])
    orders_pb2_grpc.add_OrderServiceServicer_to_server(
        MockOrderService(), server)
    server.add_insecure_port(f"[::]:{port}")

    await server.start()
    yield
    await server.stop(grace=0)


@pytest.fixture(scope="function")
async def grpc_channel():
    """
    Manages an async channel inside the test's event loop
    """
    host = os.environ.get('GRPC_SERVER_HOST', 'localhost')
    port = os.environ.get('GRPC_SERVER_PORT', '50051')
    async with grpc.aio.insecure_channel(f"{host}:{port}") as channel:
        yield channel


@pytest.fixture(scope="function")
def order_stub(grpc_channel):
    """
    Provides the active channel stub to the test
    """
    return orders_pb2_grpc.OrderServiceStub(grpc_channel)
