import requests
import os

BASE_URL = "http://localhost:8000"

def test_sse_stream():
    print("--- Testing SSE Stream (/start_job) ---")
    try:
        # Simulate the React frontend starting a job
        response = requests.post(f"{BASE_URL}/start_job", json={"prompt": "Find a 12V motor"}, stream=True)
        
        assert response.status_code == 200, f"Failed: Expected 200, got {response.status_code}"
        assert "text/event-stream" in response.headers.get("content-type", ""), "Failed: Incorrect Content-Type."
        
        print("Connection established. Listening for stream packets...")
        
        # Read the streamed lines as they arrive
        packet_count = 0
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(f"Received: {decoded_line}")
                packet_count += 1
                
        assert packet_count > 0, "Failed: Stream opened but no data was yielded."
        print("✅ SSE Stream Test Passed: Asynchronous data packets successfully received.")
    except Exception as e:
        print(f"❌ SSE Stream Test Failed: {e}")

def test_pdf_upload():
    print("\n--- Testing PDF Ingestion (/ingest_pdf) ---")
    
    # Create a dummy PDF file for testing
    dummy_file_path = "dummy_test.pdf"
    with open(dummy_file_path, "w") as f:
        f.write("This is a mock PDF file.")
        
    try:
        with open(dummy_file_path, "rb") as f:
            files = {"file": ("dummy_test.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/ingest_pdf", files=files)
            
        assert response.status_code == 200, f"Failed: Expected 200, got {response.status_code}"
        
        # Check if the file was actually saved to the temp folder
        temp_path = os.path.join("temp", "dummy_test.pdf")
        assert os.path.exists(temp_path), "Failed: File was not saved to the /temp directory."
        
        print("✅ PDF Upload Test Passed: File validated and saved to temporary storage.")
    except Exception as e:
        print(f"❌ PDF Upload Test Failed: {e}")
    finally:
        # Cleanup test files
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)
        if os.path.exists(os.path.join("temp", "dummy_test.pdf")):
            os.remove(os.path.join("temp", "dummy_test.pdf"))

if __name__ == "__main__":
    test_sse_stream()
    test_pdf_upload()