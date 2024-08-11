import argparse
from datetime import datetime
from src.dataManager import DataManager  # replace 'your_script_name' with the actual script name

# Function to test DataManager methods
def test_data_manager(start_date, end_date, contextualize):
    # Initialize the DataManager
    data_manager = DataManager()

    # Test the DataManager methods
    try:
        # Test get_data method
        full_data = data_manager.get_data(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), contextualize=contextualize)
        print("Full Data:")
        print(full_data)

    except Exception as e:
        print(f"An error occurred: {e}")

# Main function to parse arguments and run the test
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test DataManager methods")
    parser.add_argument('--start', type=str, required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end', type=str, required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--contextualize', 
                        type=lambda x: (str(x).lower() in ['true', '1']), 
                        required=False, 
                        default=True, 
                        help='True = Human defines context; False = Model')

    args = parser.parse_args()
    start_date = datetime.strptime(args.start, '%Y-%m-%d')
    end_date = datetime.strptime(args.end, '%Y-%m-%d')
    contextualize=args.contextualize 

    test_data_manager(start_date, end_date, contextualize)
