web: daphne Equb.asgi:application --port $PORT --bind 0.0.0.0 -v2
chatWorker: python manage.py runworker --settings=Equb.settings -v2
backgroundProcessor: python manage.py process_tasks
