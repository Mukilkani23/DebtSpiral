.PHONY: install install-backend install-frontend data features label train api web dev test health reset demo

install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

data:
	python -m ml.generate_dataset

features:
	python -m ml.build_features

label:
	python -m ml.label

train:
	python -m ml.train

api:
	python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

web:
	cd frontend && npm run dev

dev:
	@echo "Run 'make api' and 'make web' in separate terminals"

test:
	cd backend && python -m pytest tests/ -v

health:
	@bash scripts/healthcheck.sh

reset:
	@curl -s -X POST http://localhost:8000/reset | python -m json.tool

demo:
	@$(MAKE) reset
	@$(MAKE) health
	@echo "Open http://localhost:5173 in your browser"
