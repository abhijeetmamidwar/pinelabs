import json
import asyncio
import httpx
from pathlib import Path


async def load_sample_data(api_url: str = "http://localhost:8000", batch_size: int = 100):
    """
    Load sample_events.json data via the bulk API endpoint.
    """
    sample_file = Path(__file__).parent.parent.parent / "sample_events.json"
    
    with open(sample_file, 'r') as f:
        events = json.load(f)
    
    print(f"Loaded {len(events)} events from sample_events.json")
    
    # Process in batches
    async with httpx.AsyncClient() as client:
        total_batches = (len(events) + batch_size - 1) // batch_size
        
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} events)...")
            
            response = await client.post(
                f"{api_url}/events/bulk",
                json={"events": batch}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  Batch {batch_num}: {result['processed']} processed, {result['duplicates']} duplicates, {result['errors']} errors")
            else:
                print(f"  Batch {batch_num} failed: {response.text}")
    
    print("Data loading complete!")


if __name__ == "__main__":
    import sys
    
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    asyncio.run(load_sample_data(api_url))
