import grpc


class AsyncAuthInterceptor(grpc.aio.ServerInterceptor):
    """
    Global middleware to intercept all incoming RPCs and validate their metadata
    """

    def __init__(self, secret_token: str):
        self.secret_token = secret_token

    async def intercept_service(self, continuation, handler_call_details):
        # Extract metadata from the incoming handler details
        metadata = dict(handler_call_details.invocation_metadata)
        # Grab the authorization key
        auth_token = metadata.get('authorization')
        # Global Security check
        if auth_token != f'Bearer {self.secret_token}':
            # If auth fails, we define an alternative abort function to reject the request
            async def abort_rpc(request, context):
                await context.abort(  # type: ignore
                    grpc.StatusCode.UNAUTHENTICATED,
                    "Global Security Guard: Missing or invalid authentication token."
                )
            # Return our custom abort handler instead of letting the request proceed
            return grpc.unary_unary_rpc_method_handler(abort_rpc)

        # If auth succeeds, pass control over to the actual server method via continuation
        return await continuation(handler_call_details)
