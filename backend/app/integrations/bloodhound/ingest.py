from datetime import datetime

from app.integrations.bloodhound.client import BloodHoundClient


async def ingest_collection(collection):
    client = BloodHoundClient()
    st = client.status()
    if not st.get('enabled'):
        collection.status = 'bloodhound_disabled'
        collection.ingestion_enabled = False
        collection.ingestion_status = 'bloodhound_disabled'
        return {'status': 'bloodhound_disabled'}
    collection.ingestion_enabled = True
    collection.status = 'ingesting'
    collection.ingestion_status = 'ingesting'
    try:
        res = await client.upload_zip(collection.stored_path)
        collection.status = 'ingested'
        collection.ingestion_status = 'ingested'
        collection.ingested_at = datetime.utcnow()
        collection.ingestion_job_id = str(res.get('id') or res.get('job_id') or '')
        return res
    except Exception as e:
        collection.status = 'ingestion_failed'
        collection.ingestion_status = 'ingestion_failed'
        collection.ingestion_error = str(e)
        return {'status': 'failed', 'error': str(e)}
