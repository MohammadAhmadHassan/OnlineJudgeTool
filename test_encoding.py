"""
Test UTF-8 Encoding in Subprocess
This script tests if Unicode characters work correctly in code execution
"""
import subprocess
import sys
import os
import tempfile

# Test code with Unicode characters
test_code = """
# Test with Unicode characters
message = "Hello 世界 🌍 مرحبا"
print(message)
print("Special chars: é à ñ ü")
"""

print("Testing UTF-8 encoding in subprocess...")
print("=" * 50)

# Create temp file
temp_dir = tempfile.mkdtemp()
temp_file = os.path.join(temp_dir, "test_unicode.py")

with open(temp_file, "w", encoding='utf-8') as f:
    f.write(test_code)

# Run with UTF-8 environment (same as competitor interface)
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

try:
    process = subprocess.Popen(
        [sys.executable, temp_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env
    )
    stdout, stderr = process.communicate(timeout=5)
    
    print("✓ Test completed successfully!")
    print("\nOutput:")
    print(stdout)
    
    if stderr:
        print("\nStderr:")
        print(stderr)
        
except Exception as e:
    print(f"✗ Test failed: {e}")

finally:
    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

print("=" * 50)
print("Encoding test complete!")
