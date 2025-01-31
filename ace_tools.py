import pandas as pd
import json

def display_dataframe_to_user(title, df, max_rows=3):
    """Display a DataFrame with a title and formatted output.
    
    Args:
        title (str): Title to display above the DataFrame
        df (pd.DataFrame): DataFrame to display
        max_rows (int): Maximum number of rows to show (default: 3)
    """
    # Configure pandas display options for vertical display
    pd.set_option('display.max_rows', max_rows)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 40)  # Limit column width
    
    # Print header
    print(f"\n📊 {title}")
    print("=" * (len(title) + 4))
    
    # Display basic DataFrame info
    print(f"\n📌 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Display the DataFrame vertically
    if len(df) > 0:
        print(f"\n🔍 Data Preview (first {max_rows} rows):")
        for idx in range(min(max_rows, len(df))):
            print(f"\nRow {idx}:")
            row_data = df.iloc[idx]
            for col in df.columns:
                value = row_data[col]
                # Format nested dictionaries/lists for better readability
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                print(f"  • {col}: {value}")
            print("-" * 40) 