import os
os.environ["GEMINI_API_KEY"] = ""
from google import genai
from google.genai import types

client = genai.Client()
print("Client initialized")

task_schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "title": types.Schema(type=types.Type.STRING),
        "description": types.Schema(type=types.Type.STRING),
        "assignee": types.Schema(type=types.Type.STRING),
        "role_assigned": types.Schema(type=types.Type.STRING),
    },
    required=["title", "description", "assignee", "role_assigned"]
)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say hello",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=task_schema
        )
    )
    print("Success:", response.text)
except Exception as e:
    print("Error:", e)
