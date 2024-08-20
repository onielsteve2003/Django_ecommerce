from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework import status

def custom_exception_handler(exc, context):
    # Get the standard error response from DRF's default handler
    response = exception_handler(exc, context)
    
    # If a response was generated, modify it
    if response is not None:
        response_data = {
            "code": response.status_code,
            "message": response.data.get('detail', 'An error occurred'),
            "data": {},  # Optionally, you can include additional data here
            "success": False
        }
        # Customize specific status codes
        if response.status_code == 401:
            response_data['message'] = "Authentication credentials were not provided or are invalid"
        elif response.status_code == 403:
            response_data['message'] = "You do not have permission to perform this action"
        response.data = response_data
    else:
        # Handle cases where no response was generated (e.g., unexpected errors)
        response_data = {
            "code": 500,
            "message": "An unexpected error occurred",
            "data": {},
            "success": False
        }
        response = Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
