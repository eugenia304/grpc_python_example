import asyncio
import grpc
import os

import orders_pb2
import orders_pb2_grpc

from datetime import datetime
from dotenv import load_dotenv
from interceptors import AsyncAuthInterceptor

load_dotenv()


class MockOrderService(orders_pb2_grpc.OrderServiceServicer):

    async def GetOrderDetails(self, request, context):
        """
        Order details for a particular order ID to simulate a match.
        If the provided ID is different, return a NOT_FOUND error code
        """
        print(
            f"[Mock Server] Received request for order ID: {request.order_id}")

        if request.order_id == "ORD-123":
            return orders_pb2.OrderResponse(
                id="ORD-123",
                item_name="Coffee",
                price=29.99,
                quantity=2,
                status="SHIPPED"
            )

        await context.abort(  # type: ignore
            grpc.StatusCode.NOT_FOUND,
            f"Order with ID '{request.order_id}' not found")

    async def TrackOrder(self, request, context):
        """
        Order status sequential updates
        """
        print(f'Tracking started for ID - {request.order_id}')

        statuses = ['PENDING', 'SHIPPED', 'DELIVERED']

        for current_status in statuses:
            yield orders_pb2.OrderResponse(
                id=request.order_id,
                item_name='Coffee',
                price=29.99,
                quantity=2,
                status=current_status
            )
        # Timeout before each status update
        await asyncio.sleep(0.5)

    async def BulkCreateOrders(self, request_iterator, context):
        """
        Adding multiple orders at once and returning a single msgs afterwards
        """
        print("[Mock Server] Bulk import stream opened by client...")
        count = 0

        # Read client msgs one by one
        async for order in request_iterator:
            print(f'[Mock Server] Processing imported item: {order.item_name}')
            count += 1

        # Once the stream is done, return a signle response
        return orders_pb2.BulkImportSummary(
            total_processed=count,
            success=True,
            message=f"Successfully imported {count} orders"
        )

    async def OrderSupportChat(self, request_iterator, context):
        """
        Simulation of a live-chat where several msgs are being sent and
        the server replies to each of them individually
        """
        print("[Mock Server] Bidirectional support chat stream opened...")

        async for chat in request_iterator:
            print(
                f"[Mock Server] Received chat message for Order: {chat.order_id}")
            # Automated response
            reply = f"Automated Helpdesk: We are looking into your query regarding Order '{chat.order_id}'."
            now = datetime.now()
            date_string = now.strftime("%Y-%m-%d %H:%M:%S")

            # stream the response back to client
            yield orders_pb2.ChatResponse(
                order_id=chat.order_id,
                reply_text=reply,
                timestamp=date_string)


async def serve():
    """
    Starting the mock server at the specified host:port
    """
    token = os.environ.get('GRPC_AUTH_TOKEN', '')
    port = os.environ.get("GRPC_SERVER_PORT", "50051")

    auth_interceptor = AsyncAuthInterceptor(secret_token=token)
    # Initialize the async gRPC server
    server = grpc.aio.server(interceptors=[auth_interceptor])

    # Register mock service with the server
    orders_pb2_grpc.add_OrderServiceServicer_to_server(
        MockOrderService(), server)

    # Bind the server to port
    server.add_insecure_port(f"[::]:{port}")
    print(f"[Mock Server] Starting server on port {port}...")

    await server.start()
    # Keep the server alive
    await server.wait_for_termination()

if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("\n[Mock Server] Server stopped cleanly.")
