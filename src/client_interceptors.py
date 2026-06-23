import sys
import grpc

from google.protobuf.json_format import MessageToDict


class AsyncLoggingClientInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    """
    Global client-side middleware that automatically logs all gRPC requests,
    responses, and errors directly into the active pytest test node
    """

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        """
        Access pytest's internal state to find the current active test node
        """
        pytest_node = None
        if "pytest" in sys.modules:
            import pytest
            # Get the currently executing item from pytest
            pytest_node = getattr(pytest, "_current_test_node", None)

        # Capture outgoing request
        if pytest_node and hasattr(pytest_node, "grpc_logs"):
            pytest_node.grpc_logs["request_payload"] = MessageToDict(
                request, preserving_proto_field_name=True
            )

        try:
            response_iterator = await continuation(client_call_details, request)
            response = await response_iterator

            # Capture response on success
            if pytest_node and hasattr(pytest_node, "grpc_logs"):
                pytest_node.grpc_logs["response_payload"] = MessageToDict(
                    response, preserving_proto_field_name=True
                )

            return response

        except grpc.aio.AioRpcError as rpc_error:
            # Capture error details in case of exception
            if pytest_node and hasattr(pytest_node, "grpc_logs"):
                pytest_node.grpc_logs["error_details"] = {
                    "status_code": str(rpc_error.code()),
                    "message_details": rpc_error.details(),
                    "debug_string": rpc_error.debug_error_string()
                }
            raise rpc_error
