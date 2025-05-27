from datetime import datetime
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
def log_list_view(request, lowongan_id):
    """
    Corresponds to LogController:
    - GET /logs/student?vacancyId={lowongan_id} (list all logs for a student and vacancy)
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect("authentication:login") # Or your login URL name

    if request.method == 'GET':
        try:
            response = httpx.get(f"{BACKEND_URL}/logs/student", headers=headers,
                                 params={"vacancyId": lowongan_id})
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            logs = response.json()
            return render(request, "logs/log_list.html", {
                "logs": logs, 
                "lowongan_id": lowongan_id,
                "token": headers["Authorization"].split(" ")[1] # Token might not be needed here anymore if create form is gone
            })
        except httpx.HTTPStatusError as e:
            # You might want to pass specific error messages to the template
            return HttpResponse(f"Error fetching logs from backend: {e.response.status_code} - {e.response.text}", status=e.response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service to fetch logs.", status=503)
        except Exception as e:
            # Catch other potential errors, e.g., response.json() failing
            return HttpResponse(f"An unexpected error occurred: {str(e)}", status=500)

    return HttpResponse("Method Not Allowed", status=405)


@csrf_exempt
def log_create_view(request, lowongan_id):
    """
    Handles creation of a new log for a specific lowongan_id.
    GET: Renders the log creation form.
    POST: Submits the new log data to the backend.
    Corresponds to LogController POST /logs/{vacancyId}
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect("authentication:login")

    if request.method == 'GET':
        return render(request, "logs/log_create.html", {
            "lowongan_id": lowongan_id,
            "token": headers["Authorization"].split(" ")[1] # For CSRF or if form needs it, though headers are preferred for API
        })

    elif request.method == 'POST':
        try:
            log_date_str = request.POST.get("logDate") # "YYYY-MM-DD"
            start_time_str = request.POST.get("startTime") # "HH:MM"
            end_time_str = request.POST.get("endTime")   # "HH:MM"
            log_data = {
                "title": request.POST.get("title"),
                "description": request.POST.get("description"),
                "category": request.POST.get("category"),
                "logDate": request.POST.get("logDate"), # Expects "YYYY-MM-DD"
                "startTime": f"{log_date_str}T{start_time_str}:00", # e.g., "2023-10-27T10:00:00"
                "endTime": f"{log_date_str}T{end_time_str}:00",     # e.g., "2023-10-27T11:00:00"
                # vacancyId is part of the URL, studentId is set by backend
            }

            # Basic validation (can be more extensive)
            if not all([log_data["title"], log_data["description"], log_data["category"], log_data["logDate"], log_data["startTime"], log_data["endTime"]]):
                # Pass error message and re-render form
                return render(request, "logs/log_create.html", {
                    "lowongan_id": lowongan_id,
                    "token": headers["Authorization"].split(" ")[1],
                    "error_message": "All fields are required.",
                    "form_data": request.POST # To repopulate form
                }, status=400)

            # The backend endpoint is /logs/{vacancyId}
            response = httpx.post(f"{BACKEND_URL}/logs/{lowongan_id}", headers=headers, json=log_data)
            
            if response.status_code == 201: # 201 Created is typical for POST success
                # Redirect to the log list for this lowongan_id
                return redirect("log:log_list_view", lowongan_id=lowongan_id)
            else:
                # Pass error message and re-render form
                error_detail = response.text
                try:
                    error_json = response.json()
                    if isinstance(error_json, list):
                        error_detail = ", ".join(error_json)
                    elif isinstance(error_json, dict) and "message" in error_json:
                        error_detail = error_json["message"]
                except ValueError: # Not JSON
                    pass

                return render(request, "logs/log_create.html", {
                    "lowongan_id": lowongan_id,
                    "token": headers["Authorization"].split(" ")[1],
                    "error_message": f"Failed to create log: {response.status_code} - {error_detail}",
                    "form_data": request.POST # To repopulate form
                }, status=response.status_code)
        except httpx.RequestError:
            return render(request, "logs/log_create.html", {
                "lowongan_id": lowongan_id,
                "token": headers["Authorization"].split(" ")[1],
                "error_message": "Failed to connect to backend service to create log.",
                "form_data": request.POST # To repopulate form
            }, status=503)
        except Exception as e:
            return render(request, "logs/log_create.html", {
                "lowongan_id": lowongan_id,
                "token": headers["Authorization"].split(" ")[1],
                "error_message": f"An unexpected error occurred during log creation: {str(e)}",
                "form_data": request.POST # To repopulate form
            }, status=500)

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

            # Prepare data for the form, especially splitting datetime fields
            # Assuming backend returns startTime and endTime as full ISO strings
            # And logDate might be part of startTime or a separate YYYY-MM-DD field
            
            # If logDate is a separate field and already YYYY-MM-DD
            form_log_date = log_data.get("logDate") 

            # If startTime/endTime are full ISO strings like "2023-10-27T10:00:00"
            try:
                start_datetime_obj = datetime.fromisoformat(log_data.get("startTime", "").replace("Z", "+00:00"))
                form_start_time = start_datetime_obj.strftime('%H:%M')
                if not form_log_date: # If logDate wasn't a separate field, derive from startTime
                     form_log_date = start_datetime_obj.strftime('%Y-%m-%d')
            except ValueError:
                form_start_time = "" # Handle potential parsing errors or missing data

            try:
                end_datetime_obj = datetime.fromisoformat(log_data.get("endTime", "").replace("Z", "+00:00"))
                form_end_time = end_datetime_obj.strftime('%H:%M')
            except ValueError:
                form_end_time = ""

            context = {
                "log": log_data, # Original log data
                "form_data": { # Data formatted for form pre-population
                    "id": log_data.get("id"),
                    "title": log_data.get("title"),
                    "description": log_data.get("description"),
                    "category": log_data.get("category"),
                    "logDate": form_log_date,
                    "startTime": form_start_time,
                    "endTime": form_end_time,
                },
                "lowongan_id": log_data.get("vacancyId"), # For the "Back to list" link
                "token": headers["Authorization"].split(" ")[1]
            }
            return render(request, "logs/log_update_form.html", context)
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
            log_date_str = request.POST.get("logDate")    # "YYYY-MM-DD"
            start_time_str = request.POST.get("startTime") # "HH:MM"
            end_time_str = request.POST.get("endTime")    # "HH:MM"

            updated_data = {
                "title": request.POST.get("title"),
                "description": request.POST.get("description"),
                "category": request.POST.get("category"),
                "logDate": log_date_str,
                # Backend might expect full ISO datetime for startTime and endTime
                "startTime": f"{log_date_str}T{start_time_str}:00" if log_date_str and start_time_str else None,
                "endTime": f"{log_date_str}T{end_time_str}:00" if log_date_str and end_time_str else None,
            }
            
            # Filter out fields not provided or None, if backend expects partial updates for PATCH
            # If a field is intentionally cleared, it might need to be sent as an empty string or null
            # depending on backend API contract. For now, filtering None.
            payload = {k: v for k, v in updated_data.items() if v is not None}

            if not payload: # if all fields were None or empty after filtering
                 # Re-render form with an error if no actual data to update
                # Fetch original data again to populate form
                get_response = httpx.get(f"{BACKEND_URL}/logs/{log_id}", headers=headers)
                get_response.raise_for_status()
                original_log_data = get_response.json()
                # Prepare data for the form as in GET
                try:
                    start_datetime_obj = datetime.fromisoformat(original_log_data.get("startTime", "").replace("Z", "+00:00"))
                    form_start_time = start_datetime_obj.strftime('%H:%M')
                    form_log_date = start_datetime_obj.strftime('%Y-%m-%d')
                except ValueError: form_start_time, form_log_date = "", ""
                try:
                    end_datetime_obj = datetime.fromisoformat(original_log_data.get("endTime", "").replace("Z", "+00:00"))
                    form_end_time = end_datetime_obj.strftime('%H:%M')
                except ValueError: form_end_time = ""

                return render(request, "logs/log_update_form.html", {
                    "log": original_log_data,
                     "form_data": { # Repopulate with original data if error before sending
                        "id": original_log_data.get("id"),
                        "title": original_log_data.get("title"),
                        "description": original_log_data.get("description"),
                        "category": original_log_data.get("category"),
                        "logDate": form_log_date,
                        "startTime": form_start_time,
                        "endTime": form_end_time,
                    },
                    "lowongan_id": original_log_data.get("vacancyId"),
                    "token": headers["Authorization"].split(" ")[1],
                    "error_message": "No data provided for update. At least one field must be changed.",
                }, status=400)


            response = httpx.patch(f"{BACKEND_URL}/logs/{log_id}", headers=headers, json=payload)
            
            if response.status_code == 200 or response.status_code == 204: # 200 OK or 204 No Content
                vacancy_id_for_redirect = request.POST.get("vacancyId") # Get from hidden input if available
                if not vacancy_id_for_redirect:
                    # If PATCH response contains the updated log with vacancyId
                    try:
                        updated_log_data = response.json() # May fail if 204 No Content
                        vacancy_id_for_redirect = updated_log_data.get("vacancyId")
                    except Exception: # If response is 204 or doesn't have JSON body
                        # Try to fetch the log again to get its vacancyId
                        try:
                            refetch_response = httpx.get(f"{BACKEND_URL}/logs/{log_id}", headers=headers)
                            refetch_response.raise_for_status()
                            vacancy_id_for_redirect = refetch_response.json().get("vacancyId")
                        except Exception:
                            vacancy_id_for_redirect = None # Could not determine

                if vacancy_id_for_redirect:
                    return redirect("log:log_list_view", lowongan_id=vacancy_id_for_redirect)
                else:
                    # Fallback: attempt to get from referrer or a generic logs page.
                    # This might lead to user confusion if vacancyId is crucial for log_list_view.
                    # Consider a more robust way to always have vacancyId.
                    return redirect(request.META.get('HTTP_REFERER', '/')) 
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if isinstance(error_json, list): error_detail = ", ".join(error_json)
                    elif isinstance(error_json, dict) and "message" in error_json: error_detail = error_json["message"]
                except ValueError: pass
                
                # Re-render form with error message and submitted data
                # Fetch original data again to populate form if some fields are missing from POST
                get_response = httpx.get(f"{BACKEND_URL}/logs/{log_id}", headers=headers)
                original_log_data = get_response.json() if get_response.status_code == 200 else {}

                return render(request, "logs/log_update_form.html", {
                    "log": original_log_data, # To get ID and original vacancyId
                    "form_data": request.POST, # Repopulate with submitted data
                    "lowongan_id": original_log_data.get("vacancyId", request.POST.get("vacancyId")), # for back link
                    "token": headers["Authorization"].split(" ")[1],
                    "error_message": f"Failed to update log: {response.status_code} - {error_detail}",
                }, status=response.status_code)
        except httpx.RequestError:
            # Fetch original data for form repopulation
            try:
                get_response = httpx.get(f"{BACKEND_URL}/logs/{log_id}", headers=headers)
                original_log_data = get_response.json() if get_response.status_code == 200 else {}
                start_datetime_obj = datetime.fromisoformat(original_log_data.get("startTime", "").replace("Z", "+00:00"))
                form_s_time = start_datetime_obj.strftime('%H:%M')
                form_l_date = start_datetime_obj.strftime('%Y-%m-%d')
                end_datetime_obj = datetime.fromisoformat(original_log_data.get("endTime", "").replace("Z", "+00:00"))
                form_e_time = end_datetime_obj.strftime('%H:%M')
            except: # Broad except if fetching original data fails or parsing fails
                original_log_data = {}
                form_l_date, form_s_time, form_e_time = "", "", ""


            return render(request, "logs/log_update_form.html", {
                "log": original_log_data,
                "form_data": request.POST, # Repopulate with data user tried to submit
                 "lowongan_id": original_log_data.get("vacancyId", request.POST.get("vacancyId")),
                "token": headers["Authorization"].split(" ")[1],
                "error_message": "Failed to connect to backend service for update.",
            }, status=503)
        except Exception as e:
            # Fetch original data for form repopulation
            try:
                get_response = httpx.get(f"{BACKEND_URL}/logs/{log_id}", headers=headers)
                original_log_data = get_response.json() if get_response.status_code == 200 else {}
            except: original_log_data = {}

            return render(request, "logs/log_update_form.html", {
                "log": original_log_data,
                "form_data": request.POST,
                 "lowongan_id": original_log_data.get("vacancyId", request.POST.get("vacancyId")),
                "token": headers["Authorization"].split(" ")[1],
                "error_message": f"An unexpected error occurred during log update: {str(e)}",
            }, status=500)

    return HttpResponse("Method Not Allowed", status=405)

@csrf_exempt # If POST is from a non-Django form
def log_delete_confirmation_view(request, log_id):
    """
    Corresponds to LogController DELETE /logs/{id} (delete a log)
    GET: Display confirmation page (without fetching full log details).
    POST: Send DELETE request to backend.
    """
    auth_headers = get_auth_headers(request)
    if not auth_headers:
        return redirect("authentication:login")

    if request.method == 'GET':
        # No need to fetch log details, just pass log_id and token for the form
        return render(request, "logs/log_delete_confirm.html", {
            "log_id": log_id,
            "token": auth_headers["Authorization"].split(" ")[1] # For the form in the template
        })

    elif request.method == 'POST': # Confirmation submitted
        # Token for DELETE operation should come from the authenticated session/headers
        # The form might POST a CSRF token, but auth should be via headers
        
        try:
            response = httpx.delete(f"{BACKEND_URL}/logs/{log_id}", headers=auth_headers)
            lowongan_id_for_redirect = request.POST.get("vacancyId")
            if response.status_code in [200, 204]:
                try:
                    messages.success(request, f"Log ID {log_id} has been successfully deleted.")
                    response_data = response.json() # If backend returns data like {"message": "...", "vacancyId": ...}
                    lowongan_id_for_redirect = response_data.get("vacancyId")
                except Exception:
                    pass # No JSON body or vacancyId not present
            
                if lowongan_id_for_redirect:
                    return redirect("log:log_list_view", lowongan_id=lowongan_id_for_redirect)
                else:
                    return redirect(request.META.get('HTTP_REFERER', '/')) # Fallback
            
            elif response.status_code == 404:
                 return render(request, "logs/log_delete_confirm.html", {
                    "log_id": log_id,
                    "token": auth_headers["Authorization"].split(" ")[1],
                    "error_message": "Log not found. It may have already been deleted."
                }, status=404)
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict) and "message" in error_json:
                        error_detail = error_json["message"]
                    elif isinstance(error_json, list):
                         error_detail = ", ".join(error_json)
                except ValueError:
                    pass # Not JSON
                
                return render(request, "logs/log_delete_confirm.html", {
                    "log_id": log_id,
                    "token": auth_headers["Authorization"].split(" ")[1],
                    "error_message": f"Failed to delete log: {response.status_code} - {error_detail}"
                }, status=response.status_code)
        except httpx.RequestError:
            return render(request, "logs/log_delete_confirm.html", {
                "log_id": log_id,
                "token": auth_headers["Authorization"].split(" ")[1],
                "error_message": "Failed to connect to backend service to delete log."
            }, status=503)
        except Exception as e:
             return render(request, "logs/log_delete_confirm.html", {
                "log_id": log_id,
                "token": auth_headers["Authorization"].split(" ")[1],
                "error_message": f"An unexpected error occurred: {str(e)}"
            }, status=500)

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
                # To redirect to the specific lowongan's log list, you'd need lowongan_id.
                # This might come from the log object itself if returned by the verify endpoint.
                try:
                    verified_log_data = response.json()
                    vacancy_id = verified_log_data.get("vacancyId")
                    if vacancy_id:
                        return redirect("log:log_list", lowongan_id=vacancy_id)
                except Exception:
                    pass # Fallback
                return redirect(request.META.get('HTTP_REFERER', '/'))
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
                return redirect("log:message_list_add", log_id=log_id) # Assuming URL name
            else:
                return HttpResponse(f"Failed to add message: {response.status_code} - {response.text}", status=response.status_code)
        except httpx.RequestError:
            return HttpResponse("Failed to connect to backend service to add message.", status=503)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred while adding message: {str(e)}", status=500)

    return HttpResponse("Method Not Allowed", status=405)