import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

print('Starting batch run...')
res = client.post('/api/batch-run')
if res.status_code != 200:
    print('Failed to start batch:', res.json())
    exit(1)

run_id = res.json()['run_id']
print('Batch run started:', run_id)

status = 'running'
while status == 'running':
    res = client.get(f'/api/batch-results/{run_id}')
    data = res.json()
    status = data['status']
    print(f"Polling... Status: {status}, Processed: {data.get('cases_processed', 0)}")
    time.sleep(2)

print('Batch run completed.')
print('Recovery rate:', data.get('recovery_rate'))
print('Recovered cases:', len(data.get('recovered_list', [])))
print('Exceptions:', len(data.get('exception_list', [])))

# Print first recovered case's artifact
rec = data.get('recovered_list', [])
if rec:
    print('Sample recovered case short_url:', rec[0].get('short_url'))
else:
    print('No recovered cases.')

# Print a blocked case
exc = data.get('exception_list', [])
if exc:
    print('Sample exception rule:', exc[0].get('rule'))
