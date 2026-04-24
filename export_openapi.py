import json
from app.main import app
from fastapi.openapi.utils import get_openapi

def export_openapi():
    with open("docs/api/openapi.json", "w", encoding="utf-8") as f:
        json.dump(get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        ), f, indent=2, ensure_ascii=False)
    print("✅ Swagger (openapi.json) exportado com sucesso!")

if __name__ == "__main__":
    export_openapi()
