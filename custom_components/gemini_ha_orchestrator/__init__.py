from google import genai
from google.genai import types

# Tool definition for Gemini
save_blueprint_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="save_blueprint",
            description="Creates a new Home Assistant Blueprint and saves it to the system.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name": types.Schema(type=types.Type.STRING, description="Blueprint name (e.g. morning_routine)"),
                    "yaml_code": types.Schema(type=types.Type.STRING, description="Complete valid YAML code of the blueprint"),
                },
                required=["name", "yaml_code"],
            ),
        )
    ]
)
