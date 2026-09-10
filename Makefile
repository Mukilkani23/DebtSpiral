.PHONY: install install-backend install-frontend data features train api web dev test health reset demo

install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

data:
	cd ml && python generate_dataset.py

features:
	cd ml && python build_features.py

train:
	cd ml && python train.py

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
