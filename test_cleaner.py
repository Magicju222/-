import unittest
import pandas as pd
import numpy as np
import time
from cleaner import ExcelCleaner

class TestExcelCleaner(unittest.TestCase):
    def setUp(self):
        # Initialize cleaner without API key for header processing tests
        self.cleaner = ExcelCleaner(api_key=None)

    def test_process_headers_simple(self):
        """Test basic 2-level header merging"""
        df = pd.DataFrame([
            ['Region', 'Region', 'Date'],
            ['City', 'Sales', 'Year']
        ])
        # header_rows=[0, 1]
        result = self.cleaner.process_headers(df, [0, 1])
        expected = ['Region_City', 'Region_Sales', 'Date_Year']
        self.assertEqual(result, expected)

    def test_process_headers_horizontal_fill(self):
        """Test horizontal filling of empty header cells from left neighbor"""
        df = pd.DataFrame([
            ['Group', '', 'Other'],
            ['A', 'B', 'C']
        ])
        # Scenario:
        # Row 0: 'Group', '', 'Other' -> should fill '' with 'Group'
        # Row 1: 'A', 'B', 'C'
        # Result: 'Group_A', 'Group_B', 'Other_C'
        
        result = self.cleaner.process_headers(df, [0, 1])
        expected = ['Group_A', 'Group_B', 'Other_C']
        self.assertEqual(result, expected)

    def test_process_headers_duplicates(self):
        """Test collapsing consecutive duplicates"""
        df = pd.DataFrame([
            ['A', 'A', 'A'],
            ['A', 'B', 'B'],
            ['C', 'B', 'C']
        ])
        # Col 0: A -> A -> C => A_C (dedupe A->A)
        # Col 1: A -> B -> B => A_B (dedupe B->B)
        # Col 2: A -> B -> C => A_B_C
        result = self.cleaner.process_headers(df, [0, 1, 2])
        expected = ['A_C', 'A_B', 'A_B_C']
        self.assertEqual(result, expected)

    def test_process_headers_empty(self):
        """Test skipping empty values and horizontal propagation"""
        df = pd.DataFrame([
            ['Group', None, ''],
            ['', 'Sub', 'Val']
        ])
        # Col 0: Group -> '' => Group
        # Col 1: Group (filled from left) -> Sub => Group_Sub
        # Col 2: Group (filled from left) -> Val => Group_Val
        result = self.cleaner.process_headers(df, [0, 1])
        expected = ['Group', 'Group_Sub', 'Group_Val']
        self.assertEqual(result, expected)

    def test_process_headers_cleaning(self):
        """Test cleaning special chars and whitespace"""
        df = pd.DataFrame([
            ['  Clean  ', 'Control\nChar']
        ])
        result = self.cleaner.process_headers(df, [0])
        expected = ['Clean', 'ControlChar']
        self.assertEqual(result, expected)

    def test_process_headers_deduplication(self):
        """Test final deduplication of identical columns"""
        df = pd.DataFrame([
            ['Total', 'Total', 'Total']
        ])
        result = self.cleaner.process_headers(df, [0])
        expected = ['Total', 'Total_1', 'Total_2']
        self.assertEqual(result, expected)

    def test_process_headers_separator_slash(self):
        """Test joining headers with custom separator"""
        df = pd.DataFrame([
            ['A', 'A'],
            ['B', 'C']
        ])
        result = self.cleaner.process_headers(df, [0, 1], separator=" / ")
        expected = ['A / B', 'A / C']
        self.assertEqual(result, expected)

    def test_process_headers_deep(self):
        """Test 20-level depth"""
        # Create 20 rows, 1 column
        data = [[f"Level_{i}"] for i in range(20)]
        df = pd.DataFrame(data)
        # INCREASED MAX_LENGTH to avoid truncation error
        result = self.cleaner.process_headers(df, list(range(20)), max_length=1000)
        # Should join all 20 levels
        expected_name = "_".join([f"Level_{i}" for i in range(20)])
        self.assertEqual(result[0], expected_name)

    def test_validate_structure_logic(self):
        """Test the heuristic validation logic for header detection"""
        import pandas as pd
        
        # Scenario: 
        # Row 0: Title (Noise)
        # Row 1: Header 1 (Region, Year)
        # Row 2: Header 2 (City, 2023) -> "2023" is a year string
        # Row 3: Data (New York, 100)
        
        data = [
            ["Sales Report", "", ""],          # 0: Noise
            ["Region", "Year", "Metric"],      # 1: Header
            ["City", "2023", "Sales"],         # 2: Header (contains year)
            ["New York", 100, 500],            # 3: Data (Numeric)
            ["London", 200, 600],              # 4: Data
            ["Tokyo", 300, 700]                # 5: Data
        ]
        df = pd.DataFrame(data)
        
        # Mock AI Result: AI thinks only Row 1 is header (misses Row 2)
        ai_result = {
            "header_rows": [1],
            "data_start_row": 2, # AI thinks data starts at Row 2 (which is actually Header 2)
            "noise_rows": [0]
        }
        
        # Run validation
        new_result = self.cleaner._validate_structure(df, ai_result)
        
        # Expectation: 
        # Row 2 contains "2023" (Year pattern) -> Should be identified as Header
        # Row 3 contains 100, 500 (Numeric) -> Should be identified as Data Start
        
        self.assertIn(2, new_result["header_rows"])
        self.assertEqual(new_result["data_start_row"], 3)

    def test_detect_data_start_standard(self):
        """Test standard Header -> Data transition"""
        df = pd.DataFrame([
            ["Name", "Age", "Score"],     # 0: Header (S, S, S)
            ["Alice", 25, 90],            # 1: Data (S, N, N)
            ["Bob", 30, 85],              # 2: Data (S, N, N)
            ["Charlie", 35, 95],          # 3: Data (S, N, N)
            ["David", 40, 80]             # 4: Data (S, N, N)
        ])
        # Score[0] (Row 0 vs 1): S!=S, S!=N, S!=N -> Low
        # Score[1] (Row 1 vs 2): Match -> High
        # Score[2] (Row 2 vs 3): Match -> High
        # Score[3] (Row 3 vs 4): Match -> High
        # Stability window=3 needs Score[1], Score[2], Score[3] high.
        # So i=1. Data starts at 1.
        
        start_row = self.cleaner.detect_data_start_by_consistency(df, stability_window=3)
        self.assertEqual(start_row, 1)

    def test_detect_data_start_year_header(self):
        """Test Year Header (Int) vs Data (Int) differentiation"""
        df = pd.DataFrame([
            ["Region", 2022, 2023],       # 0: Header (S, Y, Y)
            ["North", 100, 200],          # 1: Data (S, N, N)
            ["South", 150, 250],          # 2: Data (S, N, N)
            ["East", 120, 220],           # 3: Data (S, N, N)
            ["West", 130, 230]            # 4: Data (S, N, N)
        ])
        # Row 0 types: [S, Y, Y]
        # Row 1 types: [S, N, N]
        # Row 0 vs 1: S=S, Y!=N, Y!=N. 1/3 match. Low score.
        # Row 1 vs 2: Match.
        # ...
        # Result: Data starts at 1.
        
        start_row = self.cleaner.detect_data_start_by_consistency(df, stability_window=3)
        self.assertEqual(start_row, 1)

    def test_detect_data_start_multilevel(self):
        """Test Multi-level headers"""
        df = pd.DataFrame([
            ["Title", "", ""],            # 0: Noise/Header (S, E, E)
            ["Category", "Sales", "Sales"], # 1: Header (S, S, S)
            ["Subcat", "2022", "2023"],   # 2: Header (S, Y, Y) - "2022" string -> Y
            ["A", 10, 20],                # 3: Data (S, N, N)
            ["B", 30, 40],                # 4: Data (S, N, N)
            ["C", 50, 60],                # 5: Data (S, N, N)
            ["D", 70, 80]                 # 6: Data (S, N, N)
        ])
        # Row 0 vs 1: Low
        # Row 1 vs 2: S=S, S!=Y, S!=Y -> Low
        # Row 2 vs 3: S=S, Y!=N, Y!=N -> Low
        # Row 3 vs 4: High
        # Result: Data starts at 3.
        
        start_row = self.cleaner.detect_data_start_by_consistency(df, stability_window=3)
        self.assertEqual(start_row, 3)

def benchmark_1m_columns():
    print("\nStarting Performance Benchmark (1,000,000 columns)...")
    cleaner = ExcelCleaner(api_key=None)
    
    # Generate 1M columns x 5 rows
    # We use integers to create dataframe fast, then cast to str internally
    rows = 5
    cols = 1_000_000
    
    print("Generating DataFrame...")
    # Create a simple structure: Row 0 is 'Group', Row 1 is 'Sub_i'
    # Using dictionary creation is often faster than list of lists for columnar data, 
    # but for 1M cols, numpy is best.
    
    # Strategy: Create numpy array then DF. 
    # To save memory/time, we'll repeat a smaller pattern.
    pattern_width = 1000
    pattern = np.array([f"Col_{i}" for i in range(pattern_width)])
    # Tile it to 1M
    full_row = np.tile(pattern, cols // pattern_width)
    
    data = [full_row for _ in range(rows)]
    df = pd.DataFrame(data)
    
    print(f"DataFrame Shape: {df.shape}")
    print("Running process_headers...")
    
    start_time = time.time()
    result = cleaner.process_headers(df, list(range(rows)))
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Time taken: {duration:.4f} seconds")
    
    if duration <= 0.5:
        print("✅ Performance Requirement Met (<= 500ms)")
    else:
        print(f"⚠️ Performance Warning: Exceeded 500ms by {duration - 0.5:.4f}s")
        
    # Verification
    assert len(result) == cols
    print("Result length verified.")

if __name__ == '__main__':
    # Run Unit Tests
    print("Running Unit Tests...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExcelCleaner)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Run Benchmark
    try:
        benchmark_1m_columns()
    except MemoryError:
        print("❌ Benchmark Skipped: Not enough memory to create 1M column DataFrame.")
    except Exception as e:
        print(f"❌ Benchmark Failed: {e}")