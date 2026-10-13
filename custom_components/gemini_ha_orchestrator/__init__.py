from google import genai
from google.genai import types

# Definícia nástroja, ktorú Gemini pochopí
save_blueprint_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="save_blueprint",
            description="Vytvorí nový Home Assistant Blueprint a uloží ho do systému.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name": types.Schema(type=types.Type.STRING, description="Názov blueprintu (napr. ranna_rutina)"),
                    "yaml_code": types.Schema(type=types.Type.STRING, description="Kompletný platný YAML kód blueprintu"),
                },
                required=["name", "yaml_code"],
            ),
        )
    ]
)
