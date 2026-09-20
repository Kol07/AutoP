import json

from .processingBatch_service import ProcessingBatchService

class PipelineService():
    def __init__(self, batchService: ProcessingBatchService,):
        
        self.batchService = batchService

    
    async def ingest_json(self, fileName: str, jsonBlob): # might change to zipfile
        articlesJSON = json.loads(jsonBlob)
        
        # Call create_batch(fileName) from batch service
        batch = await self.batchService.create_batch()
        
        
        # Loop through
        
            # Call create_article(processing_batch, title, content, source, published_at) from article service
        
        # Workflow 1
        
        # Workflow 2
        
        # Workflow 3
        pass