#!/bin/zsh
# filepath: /Users/jonas.avellana/development/agent-pipeline-visualizer/backend/tests/run_tests.sh

# Change to the backend directory
cd "$(dirname "$0")/.." || exit

# Set PYTHONPATH to include the current directory and parent directory
export PYTHONPATH=$PYTHONPATH:$(pwd):$(dirname $(pwd))

# Display test banner
echo "====================================="
echo "Running API Tests"
echo "====================================="

# Run all tests in the tests directory
python -m unittest discover -s tests

# Check the test result
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "\n✅ All tests passed!\n"
else
  echo -e "\n❌ Tests failed with exit code: $EXIT_CODE\n"
fi

exit $EXIT_CODE
