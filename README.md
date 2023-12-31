# IPS Recording Test Suite

## Overview
The purpose of this test suite is the validation of the functionality of the `IPSRecording` class. It includes tests for reading recordings, calculating magnetic positions, and setting rectangular grids based on recorded data.

## Running the Tests
To execute the test cases, run the following command in the terminal:
```bash
python -m unittest discover -s tests -p "TestIPSRecording.py" -v
```

## Test Cases

### `TestIPSRecording`
This class contains all the test cases for the `IPSRecording` class.

#### Methods
- `setUpClass()`: Loads the CSV files for magnetic and positional data.
- `setUp()`: Initializes the `IPSRecording` object for each test.
- `test_read_recording()`: Ensures that the recording read function returns correct data frames.
- `test_magnetics_pos_calc()`: Validates the calculation of magnetic positions.
- `test_set_rect_grid()`: Tests the functionality of setting up a rectangular grid based on the recorded data.


## Test Suite Results

Below are the results after running the test suite:

### Test for Magnetic Position Calculation

![Test for Magnetic Position Calculation](/images/test_magnetics_pos_calc.png)

### Test for Reading Recording
![Test for Reading Recording](/images/test_read_recording.png)

### Test for Setting Rectangular Grid

![Test for Setting Rectangular Grid](/images/test_set_rect_grid.png)


