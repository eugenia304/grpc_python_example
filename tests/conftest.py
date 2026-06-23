import pytest
import grpc
import os
import allure
import json

import orders_pb2_grpc

from dotenv import load_dotenv

from mock_server import MockOrderService
from interceptors import AsyncAuthInterceptor
from client_interceptors import AsyncLoggingClientInterceptor

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
    logging_interceptor = AsyncLoggingClientInterceptor()

    async with grpc.aio.insecure_channel(
        "localhost:50051",
        interceptors=[logging_interceptor]
    ) as channel:
        yield channel


@pytest.fixture(scope="function")
def order_stub(grpc_channel):
    """
    Provides the active channel stub to the test
    """
    return orders_pb2_grpc.OrderServiceStub(grpc_channel)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Automated hook that runs on test execution phases.
    Intercepts failures and prints full HTTP Request/Response logs.
    """
    # Let the test execution phase complete
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    Internal hook to store the current running node globally so 
    the interceptor can find it during execution loops
    """
    pytest._current_test_node = item  # type: ignore


@pytest.fixture(scope="function", autouse=True)
def grpc_log_bucket(request):
    """
    Provides a temporary canvas dictionary to store requests and responses for logging
    """
    request.node.grpc_logs = {
        "request_payload": None,
        "response_payload": None,
        "error_details": None
    }
    return request.node.grpc_logs


@pytest.fixture(scope="function", autouse=True)
async def api_failure_logging_teardown(request):
    yield
    # Checks if the main test call stage failed
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        test_name = request.node.name
        print(f"\n Test Failed: [{test_name}]")

        # Pull the log bucket filled during test execution
        logs = getattr(request.node, "grpc_logs", {})

        # Format the payloads for Allure readability
        formatted_log_string = json.dumps(logs, indent=2)

        # Attach the data log inside the report
        allure.attach(
            body=formatted_log_string,
            name="Logs",
            attachment_type=allure.attachment_type.JSON
        )
