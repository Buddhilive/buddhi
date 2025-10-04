from pyloid_adapter.fastapi_adapter import FastAPIAdapter, PyloidContext
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


def start(host: str, port: int):
	import uvicorn

	uvicorn.run(app, host=host, port=port)


def setup_cors():
	app.add_middleware(
		CORSMiddleware,
		allow_origins=['*'],
		allow_credentials=True,
		allow_methods=['*'],
		allow_headers=['*'],
	)


adapter = FastAPIAdapter(start, setup_cors)


@app.get('/greet')
async def greet(name: str):
	return f'Hello, {name}!'


@app.get('/create_window')
async def create_window(request: Request):
	ctx: PyloidContext = adapter.get_context(request)
	win = ctx.pyloid.create_window(title='Google Window')
	win.load_url('https://www.google.com')
	win.show_and_focus()
