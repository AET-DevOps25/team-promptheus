from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
import logging
from dotenv import load_dotenv
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.utils import get_openapi

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LangChain AI Service API",
    description="API for interacting with the LangChain AI service.",
    version="1.0.0",
)

class PredictRequest(BaseModel):
    input: str

class PredictResponse(BaseModel):
    output: str

@app.get("/health")
async def health():
    """Healthcheck endpoint"""
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """Generate a completion for the provided input using LangChain ChatOpenAI."""
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY is not set.")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured.")

    try:
        model_name = os.getenv("LANGCHAIN_MODEL_NAME", "gpt-3.5-turbo")
        chat = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name=model_name)
        message = HumanMessage(content=request.input)
        result = await chat.ainvoke([message])
        output = result.content if hasattr(result, "content") else str(result)
        logger.info({"output": output}, "Prediction successful")
        return {"output": output}
    except Exception as exc:
        logger.exception("Error during prediction")
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/doc", include_in_schema=False, response_class=JSONResponse)
async def openapi_json():
    """Return the OpenAPI specification in JSON format (alias of FastAPI's /openapi.json)."""
    return app.openapi()

@app.get("/scalar", include_in_schema=False, response_class=HTMLResponse)
async def scalar_ui():
    """Serve Scalar API reference UI."""
    html_content = """
    <!doctype html>
    <html>
    <head>
        <title>Scalar API Reference</title>
        <meta charset="utf-8" />
        <meta
        name="viewport"
        content="width=device-width, initial-scale=1" />
    </head>
    <body>
        <!-- Need a Custom Header? Check out this example https://codepen.io/scalarorg/pen/VwOXqam -->
        <script
        id="api-reference"
        data-url="/doc"></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content) 