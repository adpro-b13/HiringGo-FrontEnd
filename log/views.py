from pyexpat.errors import messages
import httpx
# import jwt # Import if you need to decode JWT for roles/claims in frontend views
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse # JsonResponse might be useful
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings # For BACKEND_URL

# Define this in your settings.py or at the top of views.py
# Example: BACKEND_URL = "http://localhost:8080/api"
# For this refactoring, I'll use a placeholder, ensure it's correctly defined in your project.
# BACKEND_URL = "http://localhost:8080"
BACKEND_URL = "http://ec2-54-208-131-6.compute-1.amazonaws.com"

# Helper function to get auth headers (optional, but keeps things DRY)
def get_auth_headers(request):
    token = request.session.get("auth_token")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

# --- Refactored Views ---

@csrf_exempt # If POST is from a non-Django form or AJAX without Django's CSRF
def log_list_and_create_view(request):
    """
    Corresponds to LogController:
    - GET /logs (list all logs)
    - POST /logs (create a new log)
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect("authentication:login") # Or your login URL name

    if request.method == 'GET':
        try:
            response = httpx.get(f"{BACKEND_URL}/logs", headers=headers)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            logs = response.json()
            return render(request, "logs/log_list.html", {"logs": logs, "token": headers["Authorization"].split(" ")[1]})
        except httpx.HTTPStatusError as e:
            # You might want to pass specific error messages to the template
            return HttpResponse(f"Error fetching logs from backend: {e.response.status_code} - {e.response.text}", status=e.response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service to fetch logs.", status=503)
        except Exception as e:
            # Catch other potential errors, e.g., response.json() failing
            return HttpResponse(f"An unexpected error occurred: {str(e)}", status=500)

    elif request.method == 'POST':
        try:
            # Assuming log data comes from form fields. Adjust keys as necessary.
            log_data = {
                "title": request.POST.get("title"),
                "content": request.POST.get("content"),
                # Add other fields relevant to your log model
            }
            # Basic validation
            if not log_data["title"] or not log_data["content"]:
                return HttpResponse("Title and content are required.", status=400)

            response = httpx.post(f"{BACKEND_URL}/logs", headers=headers, json=log_data)
            
            if response.status_code == 201 or response.status_code == 200: # 201 Created is typical for POST success
                # Redirect to the log list or the newly created log's detail page
                return redirect("logs:log_list") # Assuming 'log_list' is the name of this view's URL pattern
            else:
                return HttpResponse(f"Failed to create log: {response.status_code} - {response.text}", status=response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service to create log.", status=503)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred during log creation: {str(e)}", status=500)

    return HttpResponse("Method Not Allowed", status=405)

@csrf_exempt # If POST is from a non-Django form
def log_update_form_view(request, log_id):
    """
    Corresponds to LogController PATCH /logs/{id} (update a log)
    GET: Display form pre-filled with log data.
    POST: Process form, send PATCH request to backend.
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect("authentication:login")

    if request.method == 'GET':
        try:
            response = httpx.get(f"{BACKEND_URL}/logs/{log_id}", headers=headers)
            response.raise_for_status()
            log_data = response.json()
            return render(request, "logs/log_update_form.html", {"log": log_data, "token": headers["Authorization"].split(" ")[1]})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return HttpResponse("Log not found.", status=404)
            return HttpResponse(f"Error fetching log data: {e.response.status_code} - {e.response.text}", status=e.response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service.", status=503)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred: {str(e)}", status=500)

    elif request.method == 'POST': # Form submission, to be sent as PATCH
        try:
            updated_data = {
                "title": request.POST.get("title"),
                "content": request.POST.get("content"),
                # Add other fields that can be updated
            }
            # Filter out None values if backend expects only provided fields for PATCH
            updated_data = {k: v for k, v in updated_data.items() if v is not None}

            if not updated_data:
                 return HttpResponse("No data provided for update.", status=400)

            response = httpx.patch(f"{BACKEND_URL}/logs/{log_id}", headers=headers, json=updated_data)
            
            if response.status_code == 200 or response.status_code == 204: # 200 OK or 204 No Content
                return redirect("logs:log_list") # Or to the log detail page
            else:
                return HttpResponse(f"Failed to update log: {response.status_code} - {response.text}", status=response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service for update.", status=503)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred during log update: {str(e)}", status=500)

    return HttpResponse("Method Not Allowed", status=405)


@csrf_exempt # If POST is from a non-Django form
def log_delete_confirmation_view(request, log_id):
    """
    Corresponds to LogController DELETE /logs/{id} (delete a log)
    GET: Display confirmation page.
    POST: Send DELETE request to backend.
    """
    # For GET request, fetch token from session to display page securely
    if request.method == 'GET':
        auth_headers_session = get_auth_headers(request)
        if not auth_headers_session:
            return redirect("authentication:login")
        try:
            # Optionally fetch log details to display on confirmation page
            response = httpx.get(f"{BACKEND_URL}/logs/{log_id}", headers=auth_headers_session)
            response.raise_for_status()
            log_data = response.json()
            return render(request, "logs/log_delete_confirm.html", {"log": log_data, "log_id": log_id, "token": auth_headers_session["Authorization"].split(" ")[1]})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return HttpResponse("Log not found.", status=404)
            return HttpResponse(f"Error fetching log details: {e.response.status_code}", status=e.response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service.", status=503)


    elif request.method == 'POST': # Confirmation submitted
        # Following the example's pattern for delete, token from POST
        token = request.POST.get("token")
        if not token:
            # Fallback to session token if not in POST, or enforce POST token
            auth_headers_session = get_auth_headers(request)
            if not auth_headers_session:
                 return HttpResponse("Authentication token not provided.", status=401)
            headers_for_delete = auth_headers_session
        else:
            headers_for_delete = {"Authorization": f"Bearer {token}"}
        
        try:
            response = httpx.delete(f"{BACKEND_URL}/logs/{log_id}", headers=headers_for_delete)
            
            if response.status_code == 200 or response.status_code == 204: # 204 No Content is common for DELETE
                return redirect("logs:log_list") # Redirect to log list
            else:
                return HttpResponse(f"Failed to delete log: {response.status_code} - {response.text}", status=response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service to delete log.", status=503)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred during log deletion: {str(e)}", status=500)

    return HttpResponse("Method Not Allowed", status=405)


@csrf_exempt # POST only view
def log_verify_action_view(request, log_id):
    """
    Corresponds to LogController POST /logs/{id}/verify?action={action} (verify a log)
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect("authentication:login")

    if request.method == 'POST':
        action = request.POST.get('action') # e.g., 'ACCEPT' or 'REJECT'
        if not action:
            return HttpResponse("Action parameter is required for verification.", status=400)
        
        try:
            # Backend might expect action in query params or body.
            # Example uses query params: /verify?action={action}
            # If in body: json={"action": action}
            response = httpx.post(
                f"{BACKEND_URL}/logs/{log_id}/verify", 
                headers=headers, 
                params={"action": action} # For query parameters
            )
            
            if response.status_code == 200:
                # Redirect or return success message
                # return redirect(request.META.get('HTTP_REFERER', 'logs:log_list')) # Redirect back or to list
                return HttpResponse(f"Log {log_id} verification processed for action '{action}'.", status=200)
            else:
                return HttpResponse(f"Failed to verify log {log_id}: {response.status_code} - {response.text}", status=response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service for verification.", status=503)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred during verification: {str(e)}", status=500)

    return HttpResponse("Method Not Allowed. Use POST for verification action.", status=405)

@csrf_exempt # If POST is from a non-Django form
def message_list_and_add_view(request, log_id):
    """
    Corresponds to LogController:
    - GET /logs/{id}/messages (list messages for a log)
    - POST /logs/{id}/messages (add a message to a log)
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect("authentication:login")

    if request.method == 'GET':
        try:
            response = httpx.get(f"{BACKEND_URL}/logs/{log_id}/messages", headers=headers)
            response.raise_for_status()
            messages = response.json()
            # Also fetch the log itself if you need its details on the message page
            log_response = httpx.get(f"{BACKEND_URL}/logs/{log_id}", headers=headers)
            log_response.raise_for_status()
            log_data = log_response.json()

            return render(request, "logs/message_list.html", {"messages": messages, "log": log_data, "log_id": log_id, "token": headers["Authorization"].split(" ")[1]})
        except httpx.HTTPStatusError as e:
            return HttpResponse(f"Error fetching messages or log: {e.response.status_code} - {e.response.text}", status=e.response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service.", status=503)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred: {str(e)}", status=500)

    elif request.method == 'POST':
        message_content = request.POST.get('message')
        if not message_content:
            return HttpResponse("Message content is required.", status=400)
        
        try:
            message_data = {"content": message_content} # Or however your backend expects it
            response = httpx.post(
                f"{BACKEND_URL}/logs/{log_id}/messages", 
                headers=headers, 
                json=message_data
            )
            
            if response.status_code == 201 or response.status_code == 200:
                # Redirect back to the message list for this log
                return redirect("logs:message_list_and_add", log_id=log_id) # Assuming URL name
            else:
                return HttpResponse(f"Failed to add message: {response.status_code} - {response.text}", status=response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service to add message.", status=503)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred while adding message: {str(e)}", status=500)

    return HttpResponse("Method Not Allowed", status=405)

def view_application_status(request):
    """
    Fetches and displays the status of job applications for a MAHASISWA.
    Calls hiringultramyb13.duckdns.org:8080/status
    """
    headers = get_auth_headers(request)
    if not headers:
        # User is not authenticated, redirect to login
        messages.error(request, "You must be logged in to view application status.")
        return redirect("authentication:login") # Assuming 'authentication:login' is your login URL name

    # Check if the user role is MAHASISWA, if available in session
    # This is an optional frontend check; backend will enforce it regardless
    user_role = request.session.get("user_role")
    if user_role != 'MAHASISWA':
        messages.error(request, "Only Mahasiswa can view application status.")
        # Redirect to a relevant page, e.g., home or dashboard
        return redirect("main:home_page") # Or some other appropriate redirect

    try:
        # The endpoint is /status at hiringultramyb13.duckdns.org:8080
        response = httpx.get(f"hiringultramyb13.duckdns.org:8080/status", headers=headers)
        response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
        
        accepted_applications = response.json()
        
        return render(request, "logs/status_lamaran.html", {
            "applications": accepted_applications,
            "token": headers["Authorization"].split(" ")[1] # For potential use in template if needed
        })
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401: # Unauthorized
            messages.error(request, "Authentication failed. Please log in again.")
            return redirect("authentication:login")
        elif e.response.status_code == 403: # Forbidden (e.g., not ROLE_MAHASISWA)
            messages.error(request, f"Access denied by backend: You may not have the required role (MAHASISWA). (Status: {e.response.status_code})")
        else:
            messages.error(request, f"Error fetching application status from backend: {e.response.status_code} - {e.response.text}")
        # Render the template with an error message or redirect
        return render(request, "logs/status_lamaran.html", {"error_message": messages.get_messages(request)})
    except httpx.RequestError:
        messages.error(request, "Failed to connect to the recruitment service to fetch application status.")
        return render(request, "logs/status_lamaran.html", {"error_message": messages.get_messages(request)})
    except Exception as e:
        # Catch other potential errors, e.g., response.json() failing
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return render(request, "logs/status_lamaran.html", {"error_message": messages.get_messages(request)})